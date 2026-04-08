#!/usr/bin/env python3
"""
Telos BP Validation Service
Only validates BPs currently in the active producer schedule.
Outputs latest.json and maintains a rolling history.json.
"""

import asyncio
import aiohttp
import json
import os
import ssl
import sys
import time
from datetime import datetime, timezone

# ── Chain constants ──────────────────────────────────────────────────────────
TELOS_API        = "https://mainnet.telos.net"
MAINNET_CHAIN_ID = "4667b205c6838ef70ff7988f6e8257e8be0e1284a2f59699054a018f743b1d11"
TESTNET_CHAIN_ID = "1eaa0824707c8c16bd25145493bf062aecddfeb56c736f6ba6397f3195f33c9f"

FETCH_TIMEOUT = aiohttp.ClientTimeout(total=10)
CHECK_TIMEOUT = aiohttp.ClientTimeout(total=8)
STRICT_SSL    = ssl.create_default_context()
NO_SSL        = False

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(SCRIPT_DIR, "..", "validation", "history.json")
MAX_HISTORY  = 56   # ~14 days at 6-hour intervals

# ────────────────────────────────────────────────────────────────────────────

async def get_active_schedule(session: aiohttp.ClientSession) -> set:
    """Return the set of account names in the current active producer schedule."""
    try:
        async with session.get(
            f"{TELOS_API}/v1/chain/get_producer_schedule",
            timeout=FETCH_TIMEOUT, ssl=NO_SSL,
        ) as resp:
            data = await resp.json(content_type=None)
        active = data.get("active", {}) or {}
        producers = active.get("producers", [])
        return {p["producer_name"] for p in producers}
    except Exception as e:
        print(f"[ERROR] get_producer_schedule: {e}", file=sys.stderr)
        return set()


async def get_all_producers(session: aiohttp.ClientSession) -> list:
    """Page through get_producers to get registration info for all BPs."""
    producers, lower_bound = [], ""
    while True:
        try:
            async with session.post(
                f"{TELOS_API}/v1/chain/get_producers",
                json={"json": True, "limit": 100, "lower_bound": lower_bound},
                timeout=FETCH_TIMEOUT, ssl=NO_SSL,
            ) as resp:
                data = await resp.json(content_type=None)
        except Exception as e:
            print(f"[ERROR] get_producers: {e}", file=sys.stderr)
            break
        rows = data.get("rows", [])
        if not rows:
            break
        producers.extend(rows)
        if data.get("more"):
            lower_bound = rows[-1]["owner"]
        else:
            break
    return producers


async def fetch_json(session: aiohttp.ClientSession, url: str) -> dict | None:
    try:
        async with session.get(url, timeout=FETCH_TIMEOUT, ssl=NO_SSL) as resp:
            if resp.status == 200:
                return await resp.json(content_type=None)
    except Exception:
        pass
    return None


async def check_ssl(session: aiohttp.ClientSession, endpoint: str) -> bool:
    try:
        if not endpoint.startswith("https://"):
            return False
        async with session.get(endpoint.rstrip("/"), timeout=CHECK_TIMEOUT, ssl=STRICT_SSL) as resp:
            return resp.status < 500
    except Exception:
        return False


async def check_api(session: aiohttp.ClientSession, endpoint: str) -> tuple[bool, int]:
    url = endpoint.rstrip("/") + "/v1/chain/get_info"
    t0  = time.monotonic()
    try:
        async with session.get(url, timeout=CHECK_TIMEOUT, ssl=NO_SSL) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                if data.get("chain_id"):
                    return True, int((time.monotonic() - t0) * 1000)
    except Exception:
        pass
    return False, -1


def best_endpoint(nodes: list) -> str | None:
    for preferred in (["query"], ["producer"], ["seed"]):
        for node in nodes:
            nt    = node.get("node_type", "")
            types = nt if isinstance(nt, list) else [nt]
            if any(t in types for t in preferred):
                ep = node.get("ssl_endpoint", "").strip().rstrip("/")
                if ep:
                    return ep
    return None


async def resolve_bp_json(
    session: aiohttp.ClientSession, base_url: str
) -> tuple[dict | None, list, str | None]:
    """
    Try chains.json → mainnet entry first.
    Fall back to /bp.json directly if chains.json is missing or lacks the chain ID.
    Returns (bp_json, errors, testnet_path).
    """
    errors = []

    chains_data = await fetch_json(session, f"{base_url}/chains.json")
    if chains_data:
        chains       = chains_data.get("chains", {})
        bp_path      = chains.get(MAINNET_CHAIN_ID)
        testnet_path = chains.get(TESTNET_CHAIN_ID)
        if bp_path:
            bp_json = await fetch_json(session, base_url + bp_path)
            if bp_json:
                return bp_json, errors, testnet_path
            errors.append(f"bp.json at {base_url + bp_path} unreachable — trying /bp.json")
        else:
            errors.append("Mainnet chain ID missing from chains.json — trying /bp.json")
    else:
        errors.append("chains.json missing — trying /bp.json")

    bp_json = await fetch_json(session, f"{base_url}/bp.json")
    if bp_json:
        return bp_json, errors, None

    errors.append("/bp.json also unreachable")
    return None, errors, None


async def validate_producer(session: aiohttp.ClientSession, producer: dict) -> dict:
    owner    = producer["owner"]
    base_url = producer.get("url", "").strip().rstrip("/")

    result = {
        "owner":                owner,
        "total_votes":          producer.get("total_votes", "0"),
        "url":                  base_url,
        "is_active":            producer.get("is_active", 0),
        "sslVerified":          False,
        "apiVerified":          False,
        "apiResponseMs":        -1,
        "sslVerifiedTestNet":   False,
        "apiVerifiedTestNet":   False,
        "apiResponseMsTestNet": -1,
        "p2pEndpoint":          None,
        "org":                  {},
        "validationErrors":     [],
        "checkedAt":            datetime.now(timezone.utc).isoformat(),
    }

    if not base_url:
        result["validationErrors"] = ["No URL registered on chain"]
        return result

    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    bp_json, errors, testnet_path = await resolve_bp_json(session, base_url)

    if not bp_json:
        result["validationErrors"] = errors
        return result

    result["org"] = bp_json.get("org", {})
    nodes         = bp_json.get("nodes", [])

    for node in nodes:
        nt    = node.get("node_type", "")
        types = nt if isinstance(nt, list) else [nt]
        if "seed" in types and node.get("p2p_endpoint"):
            result["p2pEndpoint"] = node["p2p_endpoint"]
            break

    ssl_ep = best_endpoint(nodes)
    if ssl_ep:
        (ssl_ok, (api_ok, api_ms)) = await asyncio.gather(
            check_ssl(session, ssl_ep),
            check_api(session, ssl_ep),
        )
        result["sslVerified"]   = ssl_ok
        result["apiVerified"]   = api_ok
        result["apiResponseMs"] = api_ms
        if not ssl_ok:
            errors.append(f"SSL failed: {ssl_ep}")
        if not api_ok:
            errors.append(f"API failed: {ssl_ep}/v1/chain/get_info")
    else:
        errors.append("No ssl_endpoint found in bp.json nodes")

    if testnet_path:
        testnet_json = await fetch_json(session, base_url + testnet_path)
        if testnet_json:
            testnet_ep = best_endpoint(testnet_json.get("nodes", []))
            if testnet_ep:
                (ssl_ok, (api_ok, api_ms)) = await asyncio.gather(
                    check_ssl(session, testnet_ep),
                    check_api(session, testnet_ep),
                )
                result["sslVerifiedTestNet"]    = ssl_ok
                result["apiVerifiedTestNet"]    = api_ok
                result["apiResponseMsTestNet"]  = api_ms
                if not ssl_ok:
                    errors.append(f"Testnet SSL failed: {testnet_ep}")
                if not api_ok:
                    errors.append(f"Testnet API failed: {testnet_ep}")
        else:
            errors.append("Testnet bp.json missing or unreachable")

    result["validationErrors"] = errors
    return result


def update_history(results: list, generated_at: str) -> None:
    history_path = os.path.normpath(HISTORY_PATH)
    try:
        with open(history_path) as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = {"runs": []}

    snapshot = {
        "t":   generated_at,
        "bps": {
            r["owner"]: r["apiResponseMs"]
            for r in results
            if r["apiResponseMs"] > 0
        },
    }
    history["runs"].append(snapshot)
    history["runs"] = history["runs"][-MAX_HISTORY:]

    with open(history_path, "w") as f:
        json.dump(history, f, separators=(",", ":"))

    print(f"History: {len(history['runs'])} runs stored.", file=sys.stderr)


async def main():
    connector = aiohttp.TCPConnector(limit=25, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Fetch active schedule and full producer list concurrently
        print("Fetching producer schedule and list…", file=sys.stderr)
        schedule_task  = asyncio.create_task(get_active_schedule(session))
        producers_task = asyncio.create_task(get_all_producers(session))
        active_names, all_producers = await asyncio.gather(schedule_task, producers_task)

    if not active_names:
        print("[WARN] Could not fetch active schedule — validating all BPs.", file=sys.stderr)
        scheduled = all_producers
    else:
        scheduled = [p for p in all_producers if p["owner"] in active_names]
        print(f"Active schedule: {len(active_names)} BPs | matched: {len(scheduled)}", file=sys.stderr)

    connector = aiohttp.TCPConnector(limit=25, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await asyncio.gather(*[validate_producer(session, p) for p in scheduled])

    passing = sum(1 for r in results if r["sslVerified"] and r["apiVerified"])
    print(f"Done. {passing}/{len(results)} passed mainnet checks.", file=sys.stderr)

    generated_at = datetime.now(timezone.utc).isoformat()
    output = {
        "generatedAt":    generated_at,
        "totalProducers": len(results),
        "producers":      sorted(results, key=lambda r: float(r["total_votes"]), reverse=True),
    }

    print(json.dumps(output, indent=2))
    update_history(list(results), generated_at)


if __name__ == "__main__":
    asyncio.run(main())
