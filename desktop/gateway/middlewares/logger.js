/**
 * Logger Middleware — logs request lifecycle events.
 *
 * Pipeline position: first (start) and last (end).
 */

class LoggerMiddleware {
  constructor(options = {}) {
    this.verbose = options.verbose || false;
  }

  async handle(context, next) {
    const start = Date.now();
    context._loggerStart = start;

    if (this.verbose) {
      console.log(`[Gateway] → ${context.action} (${context.providerName})`);
    }

    try {
      const result = await next();
      const duration = Date.now() - start;

      if (this.verbose) {
        console.log(`[Gateway] ✓ ${context.action} ${duration}ms`);
      }

      return result;
    } catch (error) {
      const duration = Date.now() - start;

      console.error(`[Gateway] ✗ ${context.action} ${duration}ms: ${error.message}`);
      throw error;
    }
  }
}

module.exports = { LoggerMiddleware };
