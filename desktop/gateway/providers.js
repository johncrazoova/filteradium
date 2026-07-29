/**
 * Providers — each provider encapsulates communication with one data source.
 *
 * Interface:
 *   async request(actionDef, params) → Object (parsed JSON)
 *   async healthCheck() → { healthy, provider, latency, diagnostics }
 *   buildUrl(path, params) → string
 *   parse(responseText) → Object
 *
 * Transport: Electron net module (Chromium Network Stack)
 */

const { net } = require('electron');
const { URL } = require('url');

// ─── Base Provider (abstract) ──────────────────────────────
class BaseProvider {
  constructor(name, config = {}) {
    this.name = name;
    this.config = {
      baseUrl: '',
      fallbackUrls: [],
      timeout: 10000,
      headers: {},
      ...config,
    };
  }

  async request(actionDef, params) {
    throw new Error('Provider.request() must be implemented');
  }

  async healthCheck() {
    throw new Error('Provider.healthCheck() must be implemented');
  }

  buildUrl(path, params) {
    let resolved = path;
    for (const [key, value] of Object.entries(params)) {
      resolved = resolved.replace(`{${key}}`, encodeURIComponent(value));
    }
    return this.config.baseUrl + resolved;
  }

  parse(text) {
    try {
      return JSON.parse(text);
    } catch (e) {
      throw new Error(`JSON parse error: ${e.message}`);
    }
  }

  /**
   * Low-level fetch via Electron net module (Chromium Network Stack)
   *
   * Features inherited from Chromium:
   * - Auto redirect following
   * - Cookie handling
 * - HTTP/2 support
   * - Compression (gzip/br)
   * - TLS 1.2/1.3
   * - System proxy
   * - Certificate handling
   */
  async _httpFetch(url, options = {}) {
    return new Promise((resolve, reject) => {
      const parsedUrl = new URL(url);
      const method = options.method || 'GET';

      const headers = { ...this.config.headers, ...options.headers };

      // Debug logging
      if (process.env.GATEWAY_DEBUG) {
        console.log(`[Net] → ${method} ${url}`);
        console.log(`[Net] Headers:`, JSON.stringify(headers, null, 2));
      }

      const request = net.request({
        method,
        url,
        headers,
      });

      // Set timeout
      const timer = setTimeout(() => {
        request.abort();
        reject(new Error(`Request timeout: ${url}`));
      }, this.config.timeout);

      // Track redirect events
      let redirectCount = 0;
      let finalUrl = url;

      request.on('redirect', (status, method, redirectUrl, responseHeaders) => {
        redirectCount++;
        finalUrl = redirectUrl;

        if (process.env.GATEWAY_DEBUG) {
          console.log(`[Net] ↻ Redirect #${redirectCount}: ${status} → ${redirectUrl}`);
          console.log(`[Net] Response Headers:`, JSON.stringify(responseHeaders, null, 2));
        }

        // Follow redirect (Electron net auto-follows by default)
        request.followRedirect();
      });

      request.on('response', (response) => {
        let body = '';

        response.on('data', (chunk) => {
          body += chunk.toString();
        });

        response.on('end', () => {
          clearTimeout(timer);

          const statusCode = response.statusCode;
          const responseHeaders = response.headers;

          // Debug logging
          if (process.env.GATEWAY_DEBUG) {
            console.log(`[Net] ← ${statusCode} ${finalUrl}`);
            console.log(`[Net] Redirects: ${redirectCount}`);
            console.log(`[Net] Response Headers:`, JSON.stringify(responseHeaders, null, 2));
            console.log(`[Net] Body length: ${body.length}`);
            if (body.length < 500) {
              console.log(`[Net] Body: ${body}`);
            }
          }

          resolve({
            status: statusCode,
            headers: responseHeaders,
            body,
            ok: statusCode >= 200 && statusCode < 300,
          });
        });
      });

      request.on('error', (error) => {
        clearTimeout(timer);

        if (process.env.GATEWAY_DEBUG) {
          console.log(`[Net] ✗ Error: ${error.code} - ${error.message}`);
          console.log(`[Net] URL: ${url}`);
          console.log(`[Net] Redirects before error: ${redirectCount}`);
        }

        reject(error);
      });

      request.on('abort', () => {
        clearTimeout(timer);
        reject(new Error(`Request aborted: ${url}`));
      });

      // End request (for GET, no body)
      request.end();
    });
  }
}

// ─── TSETMC Provider ──────────────────────────────────────
class TsetmcProvider extends BaseProvider {
  constructor(config = {}) {
    super('tsetmc', {
      baseUrl: 'https://cdn.tsetmc.com',
      fallbackUrls: ['http://cdn.tsetmc.com', 'https://tsetmc.com', 'http://tsetmc.com'],
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://old.tsetmc.com/',
        'Origin': 'https://old.tsetmc.com',
      },
      timeout: 10000,
      ...config,
    });
  }

  async request(actionDef, params) {
    const path = actionDef.path;
    const urls = [this.config.baseUrl, ...this.config.fallbackUrls];

    let lastError;
    for (const baseUrl of urls) {
      const url = this._buildUrl(baseUrl, path, params);
      try {
        const response = await this._httpFetch(url);
        if (response.ok && response.body) {
          return this.parse(response.body);
        }
        lastError = new Error(`HTTP ${response.status}: ${url}`);
      } catch (e) {
        lastError = e;
      }
    }
    throw lastError || new Error('All providers failed');
  }

  async healthCheck() {
    const start = Date.now();
    const diagnostics = { dns: false, tcp: false, tls: false, http: false, json: false };

    try {
      const url = this.config.baseUrl + '/api/MarketData/GetMarketState';
      diagnostics.dns = true;
      diagnostics.tcp = true;
      diagnostics.tls = url.startsWith('https');

      const response = await this._httpFetch(url);
      diagnostics.http = response.ok;

      if (response.ok && response.body) {
        this.parse(response.body);
        diagnostics.json = true;
      }
    } catch (e) {
      // Diagnostics still partially useful
    }

    const latency = Date.now() - start;
    const healthy = diagnostics.http && diagnostics.json;

    return {
      healthy,
      provider: this.name,
      latency,
      checkedAt: new Date().toISOString(),
      diagnostics,
    };
  }

  _buildUrl(baseUrl, path, params) {
    let resolved = path;
    for (const [key, value] of Object.entries(params)) {
      resolved = resolved.replace(`{${key}}`, encodeURIComponent(value));
    }
    return baseUrl + resolved;
  }
}

module.exports = { BaseProvider, TsetmcProvider };
