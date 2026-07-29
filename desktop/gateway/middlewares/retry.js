/**
 * Retry Middleware — retries failed requests with exponential backoff.
 *
 * Pipeline position: after Cache, before Provider Request.
 */

class RetryMiddleware {
  constructor(options = {}) {
    this.maxRetries = options.maxRetries || 2;
    this.baseDelay = options.baseDelay || 1000;
  }

  async handle(context, next) {
    let lastError;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        context.retries = attempt;
        return await next();
      } catch (error) {
        lastError = error;

        if (attempt < this.maxRetries) {
          const delay = this.baseDelay * Math.pow(2, attempt);
          console.log(`[Gateway] Retry ${attempt + 1}/${this.maxRetries} for ${context.action} in ${delay}ms`);

          // Emit retry event if gateway is available
          if (context._gateway) {
            context._gateway.emit('request:retry', {
              action: context.action,
              attempt: attempt + 1,
              delay,
              error: error.message,
            });
          }

          await this._sleep(delay);
        }
      }
    }

    throw lastError;
  }

  _sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

module.exports = { RetryMiddleware };
