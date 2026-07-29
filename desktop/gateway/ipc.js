/**
 * IPC Gateway Handler — bridges renderer requests to the Gateway.
 *
 * This file registers ONE IPC endpoint: 'gateway:request'
 * It does NOT connect itself — main.js must call registerGatewayIPC().
 *
 * Usage in main.js:
 *   const { registerGatewayIPC } = require('./gateway/ipc');
 *   registerGatewayIPC(ipcMain, gateway);
 */

const { ipcMain } = require('electron');

/**
 * Register the single gateway IPC endpoint
 * @param {Electron ipcMain} ipc
 * @param {Gateway} gateway
 */
function registerGatewayIPC(ipc, gateway) {
  ipc.handle('gateway:request', async (event, action, params = {}) => {
    try {
      const result = await gateway.request(action, params);
      return result.toJSON();
    } catch (error) {
      return {
        ok: false,
        data: null,
        error: error.message,
        request: { provider: '', url: '', retries: 0, duration: 0, cached: false },
      };
    }
  });

  ipc.handle('gateway:health', async (event, providerName) => {
    try {
      return await gateway.healthCheck(providerName);
    } catch (error) {
      return { healthy: false, error: error.message };
    }
  });
}

module.exports = { registerGatewayIPC };
