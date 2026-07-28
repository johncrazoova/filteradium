const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // Data getters
  getStocks: () => ipcRenderer.invoke('get-stocks'),
  getStock: (insCode) => ipcRenderer.invoke('get-stock', insCode),
  getSectors: () => ipcRenderer.invoke('get-sectors'),
  getPriceHistory: (params) => ipcRenderer.invoke('get-price-history', params),
  getClientType: (params) => ipcRenderer.invoke('get-client-type', params),
  getShareholders: (params) => ipcRenderer.invoke('get-shareholders', params),
  getOrderBook: (params) => ipcRenderer.invoke('get-orderbook', params),
  getUpdateLogs: () => ipcRenderer.invoke('get-update-logs'),
  
  // Export
  exportCSV: (params) => ipcRenderer.invoke('export-csv', params),
  exportExcel: (params) => ipcRenderer.invoke('export-excel', params),
  exportExcelMulti: (params) => ipcRenderer.invoke('export-excel-multi', params),
});
