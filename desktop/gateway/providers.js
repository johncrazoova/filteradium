/**
 * Providers — each provider encapsulates communication with one data source.
 *
 * Transport: Electron net module (Chromium Network Stack)
 * Debug: Set GATEWAY_DEBUG=1 for full logging
 */

const { net } = require('electron');
const { URL } = require('url');

const DEBUG = process.env.GATEWAY_DEBUG === '1';

function log(tag, ...args) {
  if (DEBUG) console.log(`[${tag}]`, ...args);
}

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
   * Low-level fetch via Electron net module
   */
  async _httpFetch(url, options = {}) {
    return new Promise((resolve, reject) => {
      const method = options.method || 'GET';
      const headers = { ...this.config.headers, ...options.headers };

      log('NET', `→ ${method} ${url}`);
      log('NET', `Headers:`, JSON.stringify(headers, null, 2));

      const request = net.request({ method, url, headers });

      // Timeout
      const timer = setTimeout(() => {
        request.abort();
        reject(new Error(`Request timeout: ${url}`));
      }, this.config.timeout);

      // Track redirects
      let redirectCount = 0;
      let finalUrl = url;

      // ─── Electron net Events ──────────────────────────
      request.on('login', (authInfo, callback) => {
        log('NET', `🔐 login event:`, authInfo);
        callback(); // Cancel auth
      });

      request.on('redirect', (status, method, redirectUrl, responseHeaders) => {
        redirectCount++;
        finalUrl = redirectUrl;
        log('NET', `↻ Redirect #${redirectCount}: ${status} ${method}`);
        log('NET', `   Old URL: ${url}`);
        log('NET', `   New URL: ${redirectUrl}`);
        log('NET', `   Headers:`, JSON.stringify(responseHeaders, null, 2));
        request.followRedirect();
      });

      request.on('response', (response) => {
        log('NET', `← Response: ${response.statusCode}`);
        log('NET', `Headers:`, JSON.stringify(response.headers, null, 2));

        let body = '';
        response.on('data', (chunk) => { body += chunk.toString(); });

        response.on('end', () => {
          clearTimeout(timer);
          log('NET', `Body length: ${body.length}`);
          if (body.length > 0 && body.length < 500) {
            log('NET', `Body: ${body}`);
          } else if (body.length >= 500) {
            log('NET', `Body preview: ${body.substring(0, 300)}...`);
          }

          resolve({
            status: response.statusCode,
            headers: response.headers,
            body,
            ok: response.statusCode >= 200 && response.statusCode < 300,
          });
        });
      });

      request.on('error', (error) => {
        clearTimeout(timer);
        log('NET', `✗ Error: ${error.code} - ${error.message}`);
        log('NET', `URL: ${url}`);
        log('NET', `Redirects before error: ${redirectCount}`);
        reject(error);
      });

      request.on('abort', () => {
        clearTimeout(timer);
        log('NET', `⚠ Aborted: ${url}`);
        reject(new Error(`Request aborted: ${url}`));
      });

      request.on('close', () => {
        log('NET', `Close event: ${url}`);
      });

      request.on('finish', () => {
        log('NET', `Finish event: ${url}`);
      });

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

    log('PROVIDER', `request: ${actionDef.path}`);
    log('PROVIDER', `params:`, JSON.stringify(params));

    let lastError;
    for (let i = 0; i < urls.length; i++) {
      const baseUrl = urls[i];
      const url = this._buildUrl(baseUrl, path, params);
      log('PROVIDER', `Trying [${i+1}/${urls.length}]: ${url}`);

      try {
        const response = await this._httpFetch(url);
        log('PROVIDER', `Response: ${response.status} (body: ${response.body.length})`);

        if (response.ok && response.body) {
          const parsed = this.parse(response.body);
          log('PROVIDER', `✓ Success from: ${url}`);
          return parsed;
        }
        lastError = new Error(`HTTP ${response.status}: ${url}`);
        log('PROVIDER', `✗ Failed: ${lastError.message}`);
      } catch (e) {
        lastError = e;
        log('PROVIDER', `✗ Error: ${e.message}`);
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

    return { healthy, provider: this.name, latency, checkedAt: new Date().toISOString(), diagnostics };
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
