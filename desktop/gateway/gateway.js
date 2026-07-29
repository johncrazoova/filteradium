/**
 * Gateway - Provider-agnostic request router
 *
 * Routes requests to the correct Provider via Action Registry.
 * Emits events for observability. Never contains endpoint strings.
 */

const { EventEmitter } = require('events');
const { GatewayResponse } = require('./config');

class Gateway extends EventEmitter {
  constructor({ providers = {}, actions = {}, middlewares = [] } = {}) {
    super();
    this.providers = providers;   // { tsetmc: TsetmcProvider, ... }
    this.actions = actions;       // ACTION_MAP from actions.js
    this.middlewares = middlewares;
    this._defaultProvider = null;
  }

  /** Register a provider */
  registerProvider(name, provider) {
    this.providers[name] = provider;
    if (!this._defaultProvider) this._defaultProvider = name;
  }

  /** Set default provider */
  setDefaultProvider(name) {
    if (!this.providers[name]) throw new Error(`Provider "${name}" not registered`);
    this._defaultProvider = name;
  }

  /** Add middleware to pipeline */
  use(middleware) {
    this.middlewares.push(middleware);
    return this;
  }

  /**
   * Main request method
   * @param {string} action - Action name from ACTION_MAP
   * @param {Object} params - Parameters for URL templating
   * @returns {Promise<GatewayResponse>}
   */
  async request(action, params = {}) {
    const actionDef = this.actions[action];
    if (!actionDef) {
      return GatewayResponse.fail(`Unknown action: "${action}"`);
    }

    const providerName = actionDef.provider || this._defaultProvider;
    const provider = this.providers[providerName];
    if (!provider) {
      return GatewayResponse.fail(`Provider "${providerName}" not registered`);
    }

    // Build context
    const context = {
      action,
      params,
      actionDef,
      providerName,
      provider,
      cached: false,
      retries: 0,
      startTime: Date.now(),
    };

    this.emit('request:start', { action, provider: providerName });

    try {
      const result = await this._runPipeline(context);
      const duration = Date.now() - context.startTime;

      this.emit('request:success', {
        action,
        provider: providerName,
        duration,
        cached: context.cached,
      });

      return GatewayResponse.ok(result, {
        provider: providerName,
        url: context.resolvedUrl || '',
        retries: context.retries,
        duration,
        cached: context.cached,
      });
    } catch (error) {
      const duration = Date.now() - context.startTime;

      this.emit('request:error', {
        action,
        provider: providerName,
        duration,
        error: error.message,
      });

      return GatewayResponse.fail(error.message, {
        provider: providerName,
        url: context.resolvedUrl || '',
        retries: context.retries,
        duration,
      });
    }
  }

  /**
   * Health check for a specific provider or all providers
   */
  async healthCheck(providerName) {
    const targets = providerName
      ? { [providerName]: this.providers[providerName] }
      : this.providers;

    const results = {};
    for (const [name, provider] of Object.entries(targets)) {
      if (provider && typeof provider.healthCheck === 'function') {
        results[name] = await provider.healthCheck();
      } else {
        results[name] = { healthy: false, error: 'Provider not available' };
      }
    }
    return results;
  }

  /** Run middleware pipeline */
  async _runPipeline(context) {
    const middlewares = [...this.middlewares];

    const dispatch = async (index) => {
      if (index >= middlewares.length) {
        // End of pipeline — execute provider request
        return context.provider.request(context.actionDef, context.params);
      }
      const mw = middlewares[index];
      return mw.handle(context, () => dispatch(index + 1));
    };

    return dispatch(0);
  }
}

module.exports = { Gateway };
