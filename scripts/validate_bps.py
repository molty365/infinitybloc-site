#!/usr/bin/env python3
"""
Telos BP Validation Service
Fetches all active block producers, validates their bp.json endpoints, SSL,
and API health. Outputs a single JSON file consumed by the validator UI.
"""

import asyncio
import aiohttp
import json
import ssl
import sys
from datetime import datetime, timezone

# ── Chain constants ─────────────────────────────────────────────────────────
TELOS_API         = "https://mainnet.telos.net"
MAINNET_CHAIN_ID  = "4667b205c6838ef70ff7988f6e8257e8be0e1284a2f59699054a018f743b1d11"
TESTNET_CHAIN_ID  = "1eaa0824707c8c16bd25145493bf062aecddfeb56c736f6ba6397f3195f33c9f"

# ── Timeouts ────────────────────────────────────────────────────────────────
FETCH_TIMEOUT = aiohttp.ClientTimeout(total=10)
CHECK_TIMEOUT = aiohttp.ClientTimeout(total=8)

# ── SSL context for strict verification ─────────────────────────────────────
STRICT_SSL = ssl.create_default_context()
NO_SSL     = False   # used when fetching bp.json (http is acceptable)

# ────────────────────────────────────────────────────────────────────────────

async def get_all_producers(session: aiohttp.ClientSession) -> list:
    """Page through get_producers until we have every active BP."""
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
    """Fetch a JSON document, return None on any failure."""
    try:
        async with session.get(url, timeout=FETCH_TIMEOUT, ssl=NO_SSL) as resp:
            if resp.status == 200:
                return await resp.json(content_type=None)
    except Exception:
        pass
    return None


async def check_ssl(session: aiohttp.ClientSession, endpoint: str) -> bool:
    """Return True if endpoint has a valid SSL certificate and returns HTTP < 500."""
    try:
        url = endpoint.rstrip("/")
        if not url.startswith("https://"):
            return False
        async with session.get(url, timeout=CHECK_TIMEOUT, ssl=STRICT_SSL) as resp:
            return resp.status < 500
    except Exception:
        return False


async def check_api(session: aiohttp.ClientSession, endpoint: str) -> bool:
    """Return True if /v1/chain/get_info returns a valid chain_id."""
    try:
        url = endpoint.rstrip("/") + "/v1/chain/get_info"
        async with session.get(url, timeout=CHECK_TIMEOUT, ssl=NO_SSL) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                return bool(data.get("chain_id"))
    except Exception:
        pass
    return False


def best_endpoint(nodes: list) -> str | None:
    """Pick the best ssl_endpoint from a list of bp.json nodes."""
    for node_type in (["query"], ["producer"], ["seed"]):
        for node in nodes:
            nt = node.get("node_type", "")
            types = nt if isinstance(nt, list) else [nt]
            if any(t in types for t in node_type):
                ep = node.get("ssl_endpoint", "").strip().rstrip("/")
                if ep:
                    return ep
    return None


async def validate_producer(session: aiohttp.ClientSession, producer: dict) -> dict:
    """Run all checks for a single producer and return a result dict."""
    owner = producer["owner"]
    base_url = producer.get("url", "").strip().rstrip("/")
    errors = []

    result = {
        "owner":              owner,
        "total_votes":        producer.get("total_votes", "0"),
        "url":                base_url,
        "is_active":          producer.get("is_active", 0),
        "sslVerified":        False,
        "apiVerified":        False,
        "sslVerifiedTestNet": False,
        "apiVerifiedTestNet": False,
        "p2pEndpoint":        None,
        "org":                {},
        "validationErrors":   [],
        "checkedAt":          datetime.now(timezone.utc).isoformat(),
    }

    if not base_url:
        result["validationErrors"] = ["No URL registered on chain"]
        return result

    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    # 1. chains.json
    chains_data = await fetch_json(session, f"{base_url}/chains.json")
    if not chains_data:
        result["validationErrors"] = ["chains.json missing or unreachable"]
        return result

    chains = chains_data.get("chains", {})

    # 2. Mainnet bp.json
    bp_path = chains.get(MAINNET_CHAIN_ID)
    if not bp_path:
        result["validationErrors"] = ["Mainnet chain ID not found in chains.json"]
        return result

    bp_json = await fetch_json(session, base_url + bp_path)
    if not bp_json:
        result["validationErrors"] = [f"bp.json at {base_url + bp_path} missing or unreachable"]
        return result

    result["org"] = bp_json.get("org", {})
    nodes = bp_json.get("nodes", [])

    # Collect p2p endpoint for display
    for node in nodes:
        nt = node.get("node_type", "")
        types = nt if isinstance(nt, list) else [nt]
        if "seed" in types and node.get("p2p_endpoint"):
            result["p2pEndpoint"] = node["p2p_endpoint"]
            break

    # 3. Mainnet SSL + API
    ssl_ep = best_endpoint(nodes)
    if ssl_ep:
        ssl_ok, api_ok = await asyncio.gather(
            check_ssl(session, ssl_ep),
            check_api(session, ssl_ep),
        )
        result["sslVerified"] = ssl_ok
        result["apiVerified"] = api_ok
        if not ssl_ok:
            errors.append(f"SSL failed: {ssl_ep}")
        if not api_ok:
            errors.append(f"API failed: {ssl_ep}/v1/chain/get_info")
    else:
        errors.append("No ssl_endpoint found in any bp.json node")

    # 4. Testnet bp.json + checks (optional)
    testnet_path = chains.get(TESTNET_CHAIN_ID)
    if testnet_path:
        testnet_json = await fetch_json(session, base_url + testnet_path)
        if testnet_json:
            testnet_ep = best_endpoint(testnet_json.get("nodes", []))
            if testnet_ep:
                ssl_ok, api_ok = await asyncio.gather(
                    check_ssl(session, testnet_ep),
                    check_api(session, testnet_ep),
                )
                result["sslVerifiedTestNet"] = ssl_ok
                result["apiVerifiedTestNet"] = api_ok
                if not ssl_ok:
                    errors.append(f"Testnet SSL failed: {testnet_ep}")
                if not api_ok:
                    errors.append(f"Testnet API failed: {testnet_ep}/v1/chain/get_info")
        else:
            errors.append("Testnet bp.json missing or unreachable")

    result["validationErrors"] = errors
    return result


async def main():
    # Shared connector with reasonable concurrency limit
    connector = aiohttp.TCPConnector(limit=25, ssl=False)

    async with aiohttp.ClientSession(connector=connector) as session:
        print("Fetching producer list…", file=sys.stderr)
        producers = await get_all_producers(session)
        print(f"Validating {len(producers)} producers…", file=sys.stderr)

        tasks   = [validate_producer(session, p) for p in producers]
        results = await asyncio.gather(*tasks)

    passed    = sum(1 for r in results if r["sslVerified"] and r["apiVerified"])
    print(f"Done. {passed}/{len(results)} passed mainnet checks.", file=sys.stderr)

    output = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totalProducers": len(results),
        "producers": sorted(results, key=lambda r: float(r["total_votes"]), reverse=True),
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
