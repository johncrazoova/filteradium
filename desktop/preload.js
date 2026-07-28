const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getStocks: () => ipcRenderer.invoke('get-stocks'),
  getSectors: () => ipcRenderer.invoke('get-sectors'),
  getStats: () => ipcRenderer.invoke('get-stats'),
  testConnection: () => ipcRenderer.invoke('test-connection'),

  fetchAllStocks: () => ipcRenderer.invoke('fetch-all-stocks'),
  fetchStockData: (params) => ipcRenderer.invoke('fetch-stock-data', params),

  getPriceHistory: (params) => ipcRenderer.invoke('get-price-history', params),
  getClientType: (params) => ipcRenderer.invoke('get-client-type-local', params),
  getShareholders: (params) => ipcRenderer.invoke('get-shareholders-local', params),

  exportCSV: (params) => ipcRenderer.invoke('export-csv', params),
  exportExcel: (params) => ipcRenderer.invoke('export-excel', params),
  exportExcelMulti: (params) => ipcRenderer.invoke('export-excel-multi', params),

  onProgress: (cb) => ipcRenderer.on('fetch-progress', (e, data) => cb(data)),
});
