/**
 * Gateway module — exports everything needed to initialize the gateway.
 */

const { Gateway } = require('./gateway');
const { TsetmcProvider } = require('./providers');
const { GatewayResponse } = require('./config');
const { ACTION_MAP } = require('./actions');
const { HealthChecker } = require('./health');

// Middlewares
const { LoggerMiddleware } = require('./middlewares/logger');
const { RetryMiddleware } = require('./middlewares/retry');
const { CacheMiddleware } = require('./middlewares/cache');
const { RateLimiterMiddleware } = require('./middlewares/rateLimiter');

/**
 * Create a pre-configured Gateway with TSETMC provider
 */
function createDefaultGateway(config = {}) {
  const gateway = new Gateway({
    actions: ACTION_MAP,
  });

  // Register TSETMC provider
  const tsetmc = new TsetmcProvider(config.tsetmc || {});
  gateway.registerProvider('tsetmc', tsetmc);
  gateway.setDefaultProvider('tsetmc');

  // Add middleware pipeline
  gateway.use(new LoggerMiddleware({ verbose: config.verbose || false }));
  gateway.use(new RateLimiterMiddleware({ maxPerSecond: config.rateLimit || 5 }));
  gateway.use(new CacheMiddleware());
  gateway.use(new RetryMiddleware({ maxRetries: config.retries || 2 }));

  return gateway;
}

module.exports = {
  Gateway,
  TsetmcProvider,
  GatewayResponse,
  ACTION_MAP,
  HealthChecker,
  LoggerMiddleware,
  RetryMiddleware,
  CacheMiddleware,
  RateLimiterMiddleware,
  createDefaultGateway,
};
