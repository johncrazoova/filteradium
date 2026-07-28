const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // DB getters
  getStocks: () => ipcRenderer.invoke('get-stocks'),
  getSectors: () => ipcRenderer.invoke('get-sectors'),
  getStats: () => ipcRenderer.invoke('get-stats'),
  getUpdateLog: () => ipcRenderer.invoke('get-update-log'),

  // Fetch from TSETMC
  fetchAllStocks: () => ipcRenderer.invoke('fetch-all-stocks'),
  fetchHistory: (insCode) => ipcRenderer.invoke('fetch-history', insCode),
  fetchClientType: (insCode) => ipcRenderer.invoke('fetch-client-type', insCode),
  fetchShareholders: (insCode) => ipcRenderer.invoke('fetch-shareholders', insCode),

  // Local DB queries
  getPriceHistory: (params) => ipcRenderer.invoke('get-price-history', params),
  getClientType: (params) => ipcRenderer.invoke('get-client-type-local', params),
  getShareholders: (params) => ipcRenderer.invoke('get-shareholders-local', params),

  // Export
  exportCSV: (params) => ipcRenderer.invoke('export-csv', params),
  exportExcel: (params) => ipcRenderer.invoke('export-excel', params),
});
