/**
 * GatewayResponse — standardized response shape.
 * Never return raw fetch responses.
 */

class GatewayResponse {
  constructor({ ok, data, error, request }) {
    this.ok = ok;
    this.data = data;
    this.error = error;
    this.request = request;
  }

  static ok(data, meta = {}) {
    return new GatewayResponse({
      ok: true,
      data,
      error: null,
      request: {
        provider: meta.provider || '',
        url: meta.url || '',
        retries: meta.retries || 0,
        duration: meta.duration || 0,
        cached: meta.cached || false,
      },
    });
  }

  static fail(error, meta = {}) {
    return new GatewayResponse({
      ok: false,
      data: null,
      error: error || 'Unknown error',
      request: {
        provider: meta.provider || '',
        url: meta.url || '',
        retries: meta.retries || 0,
        duration: meta.duration || 0,
        cached: false,
      },
    });
  }

  toJSON() {
    return {
      ok: this.ok,
      data: this.data,
      error: this.error,
      request: this.request,
    };
  }
}

/**
 * Provider interface — every provider must implement these methods.
 * This is a documentation-only interface (Node.js has no formal interface).
 *
 * class ProviderInterface {
 *   async request(actionDef, params) → Object
 *   async healthCheck() → { healthy, provider, latency, diagnostics }
 *   buildUrl(path, params) → string
 *   parse(responseText) → Object
 * }
 */

module.exports = { GatewayResponse };
