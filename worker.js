/**
 * Cloudflare Worker: infinitybloc.io → Netlify proxy
 * Forwards all requests to the Netlify origin while preserving
 * CORS headers for bp.json, chains.json, and telos-testnet.json.
 */

const NETLIFY_ORIGIN = "https://infinitybloc-site.netlify.app";

const CORS_PATHS = ["/bp.json", "/chains.json", "/telos-testnet.json"];

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Build the proxied URL pointing at Netlify
    const originUrl = NETLIFY_ORIGIN + url.pathname + url.search;

    // Override the Host header so Netlify accepts the request
    const modifiedHeaders = new Headers(request.headers);
    modifiedHeaders.set("Host", "infinitybloc-site.netlify.app");

    const proxyRequest = new Request(originUrl, {
      method: request.method,
      headers: modifiedHeaders,
      body: request.method !== "GET" && request.method !== "HEAD" ? request.body : undefined,
      redirect: "follow",
    });

    let response = await fetch(proxyRequest);

    // Add CORS headers for the JSON endpoint files
    if (CORS_PATHS.includes(url.pathname)) {
      const newHeaders = new Headers(response.headers);
      newHeaders.set("Access-Control-Allow-Origin", "*");
      newHeaders.set("Access-Control-Allow-Methods", "GET, OPTIONS");
      newHeaders.set("Access-Control-Allow-Headers", "Content-Type");
      response = new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders,
      });
    }

    return response;
  },
};
