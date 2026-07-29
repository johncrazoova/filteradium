/**
 * RateLimiter Middleware — limits requests per second.
 *
 * Pipeline position: after Logger(start), before Cache.
 */

class RateLimiterMiddleware {
  constructor(options = {}) {
    this.maxPerSecond = options.maxPerSecond || 5;
    this.queue = [];
    this.running = 0;
  }

  async handle(context, next) {
    await this._acquire();
    try {
      return await next();
    } finally {
      this._release();
    }
  }

  async _acquire() {
    while (this.running >= this.maxPerSecond) {
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    this.running++;
  }

  _release() {
    this.running = Math.max(0, this.running - 1);
  }
}

module.exports = { RateLimiterMiddleware };
