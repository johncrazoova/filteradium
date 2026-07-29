/**
 * IPC Gateway Handler — bridges renderer requests to the Gateway.
 *
 * This file registers ONE IPC endpoint: 'gateway:request'
 * It does NOT connect itself — main.js must call registerGatewayIPC().
 */

function registerGatewayIPC(ipcMain, gateway) {
  ipcMain.handle('gateway:request', async (event, action, params = {}) => {
    try {
      // Validate action exists
      if (!action || typeof action !== 'string') {
        return { ok: false, data: null, error: 'Invalid action: must be a string', request: { provider: '', url: '', retries: 0, duration: 0, cached: false } };
      }

      // Validate params
      if (params && typeof params !== 'object') {
        return { ok: false, data: null, error: 'Invalid params: must be an object', request: { provider: '', url: '', retries: 0, duration: 0, cached: false } };
      }

      const result = await gateway.request(action, params || {});
      return result.toJSON();
    } catch (error) {
      console.error(`[Gateway:IPC] Error: ${error.message}`);
      return { ok: false, data: null, error: error.message, request: { provider: '', url: '', retries: 0, duration: 0, cached: false } };
    }
  });
}

module.exports = { registerGatewayIPC };
