const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow () {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    title: 'Filteradium',
    icon: path.join(__dirname, '..', 'icons', 'icon-192.png')
  })

  // Load from local files (no server needed!)
  mainWindow.loadFile(path.join(__dirname, '..', 'index.html'))
  
  mainWindow.setMenuBarVisibility(false)
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => app.quit())
