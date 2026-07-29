const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // ========== Gateway (New) ==========
  request: (action, params) => ipcRenderer.invoke('gateway:request', action, params),

  // ========== Database (Existing — unchanged) ==========
  getStocks: () => ipcRenderer.invoke('get-stocks'),
  getSectors: () => ipcRenderer.invoke('get-sectors'),
  getStats: () => ipcRenderer.invoke('get-stats'),

  saveStocks: (stocks) => ipcRenderer.invoke('save-stocks', stocks),
  savePriceHistory: (params) => ipcRenderer.invoke('save-price-history', params),
  saveClientType: (params) => ipcRenderer.invoke('save-client-type', params),
  saveShareholders: (params) => ipcRenderer.invoke('save-shareholders', params),

  getPriceHistory: (params) => ipcRenderer.invoke('get-price-history', params),
  getClientType: (params) => ipcRenderer.invoke('get-client-type-local', params),
  getShareholders: (params) => ipcRenderer.invoke('get-shareholders-local', params),

  exportCSV: (params) => ipcRenderer.invoke('export-csv', params),
  exportExcelMulti: (params) => ipcRenderer.invoke('export-excel-multi', params),

  onProgress: (cb) => ipcRenderer.on('fetch-progress', (e, data) => cb(data)),
});
