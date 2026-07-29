/**
 * Providers — each provider encapsulates communication with one data source.
 *
 * Interface:
 *   async request(actionDef, params) → Object (parsed JSON)
 *   async healthCheck() → { healthy, provider, latency, diagnostics }
 *   buildUrl(path, params) → string
 *   parse(responseText) → Object
 */

const https = require('https');
const http = require('http');
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
    // Replace {param} placeholders
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

  /** Low-level fetch via Node.js http/https */
  async _httpFetch(url, options = {}) {
    return new Promise((resolve, reject) => {
      const parsedUrl = new URL(url);
      const client = parsedUrl.protocol === 'https:' ? https : http;

      const reqOptions = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port,
        path: parsedUrl.pathname + parsedUrl.search,
        method: options.method || 'GET',
        headers: { ...this.config.headers, ...options.headers },
        timeout: this.config.timeout,
      };

      const timer = setTimeout(() => {
        req.destroy();
        reject(new Error(`Request timeout: ${url}`));
      }, this.config.timeout);

      const req = client.request(reqOptions, (res) => {
        let body = '';
        res.on('data', (chunk) => (body += chunk));
        res.on('end', () => {
          clearTimeout(timer);
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body,
            ok: res.statusCode >= 200 && res.statusCode < 300,
          });
        });
      });

      req.on('error', (e) => {
        clearTimeout(timer);
        reject(e);
      });

      req.on('timeout', () => {
        clearTimeout(timer);
        req.destroy();
        reject(new Error(`Socket timeout: ${url}`));
      });

      req.end();
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
      // Try the simplest endpoint
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
