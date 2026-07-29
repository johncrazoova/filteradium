/**
 * Health Check — standalone utility for provider health diagnostics.
 *
 * Returns detailed health status for a provider or all providers.
 */

class HealthChecker {
  constructor(gateway) {
    this.gateway = gateway;
  }

  /**
   * Check health of a specific provider
   * @param {string} providerName
   * @returns {Promise<HealthStatus>}
   */
  async checkProvider(providerName) {
    const provider = this.gateway.providers[providerName];
    if (!provider) {
      return {
        healthy: false,
        provider: providerName,
        latency: 0,
        checkedAt: new Date().toISOString(),
        error: `Provider "${providerName}" not registered`,
        diagnostics: { dns: false, tcp: false, tls: false, http: false, json: false },
      };
    }

    if (typeof provider.healthCheck !== 'function') {
      return {
        healthy: false,
        provider: providerName,
        latency: 0,
        checkedAt: new Date().toISOString(),
        error: 'Provider does not implement healthCheck()',
        diagnostics: { dns: false, tcp: false, tls: false, http: false, json: false },
      };
    }

    return provider.healthCheck();
  }

  /**
   * Check health of all registered providers
   * @returns {Promise<Object>} { providerName: HealthStatus }
   */
  async checkAll() {
    const results = {};
    for (const name of Object.keys(this.gateway.providers)) {
      results[name] = await this.checkProvider(name);
    }
    return results;
  }

  /**
   * Quick overall health status
   * @returns {Promise<{ healthy: boolean, providers: Object }>}
   */
  async quickCheck() {
    const providers = await this.checkAll();
    const healthy = Object.values(providers).some((p) => p.healthy);
    return { healthy, providers };
  }
}

module.exports = { HealthChecker };
