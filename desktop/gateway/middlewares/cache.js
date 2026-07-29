/**
 * Cache Middleware — caches responses based on action TTL policy.
 *
 * Pipeline position: after RateLimiter, before Retry.
 *
 * Fixes:
 * - In-flight dedup: concurrent requests for same key share one promise
 * - No double-write: result stored only once per request lifecycle
 */

class CacheMiddleware {
  constructor(options = {}) {
    this.store = new Map();
    this.inflight = new Map();  // Dedup concurrent requests
    this.defaultTTL = options.defaultTTL || 300000; // 5 min
  }

  async handle(context, next) {
    const actionDef = context.actionDef;

    // Check if caching is enabled for this action
    if (!actionDef.cache || !actionDef.cache.enabled) {
      return next();
    }

    // Build cache key from action + params
    const key = this._buildKey(context.action, context.params);

    // 1. Return cached if valid
    const cached = this.store.get(key);
    if (cached && Date.now() < cached.expiresAt) {
      context.cached = true;

      if (context._gateway) {
        context._gateway.emit('request:cached', { action: context.action });
      }

      return cached.data;
    }

    // 2. Dedup: if same key is in-flight, wait for it
    if (this.inflight.has(key)) {
      return this.inflight.get(key);
    }

    // 3. Execute and cache (only once per key)
    const promise = this._executeAndCache(key, context, next, actionDef);
    this.inflight.set(key, promise);

    try {
      return await promise;
    } finally {
      this.inflight.delete(key);
    }
  }

  async _executeAndCache(key, context, next, actionDef) {
    const result = await next();

    // Only cache once — if result is valid
    if (result !== undefined && result !== null) {
      const ttl = actionDef.cache?.ttl || this.defaultTTL;
      this.store.set(key, {
        data: result,
        expiresAt: Date.now() + ttl,
      });
    }

    // Cleanup expired entries periodically
    this._cleanup();

    return result;
  }

  _buildKey(action, params) {
    const sorted = Object.entries(params)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}=${v}`)
      .join('&');
    return `${action}:${sorted}`;
  }

  _cleanup() {
    const now = Date.now();
    for (const [key, entry] of this.store.entries()) {
      if (now >= entry.expiresAt) {
        this.store.delete(key);
      }
    }
  }

  /** Clear all cached entries */
  clear() {
    this.store.clear();
  }

  /** Clear cache for a specific action */
  clearAction(action) {
    for (const key of this.store.keys()) {
      if (key.startsWith(action + ':')) {
        this.store.delete(key);
      }
    }
  }
}

module.exports = { CacheMiddleware };
