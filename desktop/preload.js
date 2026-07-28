// Preload script for Filteradium Desktop
// This runs in the renderer process before the web page loads

const { contextBridge } = require('electron');

// Expose safe APIs to the renderer
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  isElectron: true
});
