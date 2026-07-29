/**
 * Cache Middleware — caches responses based on action TTL policy.
 *
 * Pipeline position: after RateLimiter, before Retry.
 */

class CacheMiddleware {
  constructor(options = {}) {
    this.store = new Map();
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
    const cached = this.store.get(key);

    // Return cached if valid
    if (cached && Date.now() < cached.expiresAt) {
      context.cached = true;

      if (context._gateway) {
        context._gateway.emit('request:cached', { action: context.action });
      }

      return cached.data;
    }

    // Execute and cache
    const result = await next();

    const ttl = actionDef.cache.ttl || this.defaultTTL;
    this.store.set(key, {
      data: result,
      expiresAt: Date.now() + ttl,
    });

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
