const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const Database = require('better-sqlite3');
const XLSX = require('xlsx');
const fs = require('fs');

let mainWindow;
let db;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    title: 'Filteradium Exporter',
    icon: path.join(__dirname, '..', 'icon-512.png'),
    backgroundColor: '#0B0B1A'
  });

  mainWindow.loadFile('index.html');
  mainWindow.setMenuBarVisibility(false);
}

function initDatabase() {
  const dbPath = path.join(__dirname, '..', 'data', 'filteradium.db');
  if (fs.existsSync(dbPath)) {
    db = new Database(dbPath, { readonly: true });
    console.log('Database connected:', dbPath);
  } else {
    console.error('Database not found:', dbPath);
  }
}

// ========== IPC Handlers ==========

// Get all stocks
ipcMain.handle('get-stocks', () => {
  if (!db) return [];
  try {
    return db.prepare('SELECT * FROM stocks ORDER BY symbol').all();
  } catch (e) {
    console.error(e);
    return [];
  }
});

// Get stock by ins_code
ipcMain.handle('get-stock', (event, insCode) => {
  if (!db) return null;
  try {
    return db.prepare('SELECT * FROM stocks WHERE ins_code = ?').get(insCode);
  } catch (e) {
    console.error(e);
    return null;
  }
});

// Get sectors
ipcMain.handle('get-sectors', () => {
  if (!db) return [];
  try {
    return db.prepare('SELECT DISTINCT sector FROM stocks WHERE sector IS NOT NULL ORDER BY sector').all();
  } catch (e) {
    console.error(e);
    return [];
  }
});

// Get price history
ipcMain.handle('get-price-history', (event, { insCodes, startDate, endDate }) => {
  if (!db) return [];
  try {
    let query = 'SELECT * FROM price_history WHERE 1=1';
    const params = [];

    if (insCodes && insCodes.length > 0) {
      query += ` AND ins_code IN (${insCodes.map(() => '?').join(',')})`;
      params.push(...insCodes);
    }

    if (startDate) {
      query += ' AND date >= ?';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND date <= ?';
      params.push(endDate);
    }

    query += ' ORDER BY ins_code, date';
    return db.prepare(query).all(...params);
  } catch (e) {
    console.error(e);
    return [];
  }
});

// Get client type history
ipcMain.handle('get-client-type', (event, { insCodes, startDate, endDate }) => {
  if (!db) return [];
  try {
    let query = 'SELECT * FROM client_type_history WHERE 1=1';
    const params = [];

    if (insCodes && insCodes.length > 0) {
      query += ` AND ins_code IN (${insCodes.map(() => '?').join(',')})`;
      params.push(...insCodes);
    }

    if (startDate) {
      query += ' AND date >= ?';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND date <= ?';
      params.push(endDate);
    }

    query += ' ORDER BY ins_code, date';
    return db.prepare(query).all(...params);
  } catch (e) {
    console.error(e);
    return [];
  }
});

// Get shareholder snapshots
ipcMain.handle('get-shareholders', (event, { insCodes, startDate, endDate }) => {
  if (!db) return [];
  try {
    let query = 'SELECT * FROM shareholder_snapshots WHERE 1=1';
    const params = [];

    if (insCodes && insCodes.length > 0) {
      query += ` AND ins_code IN (${insCodes.map(() => '?').join(',')})`;
      params.push(...insCodes);
    }

    if (startDate) {
      query += ' AND date >= ?';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND date <= ?';
      params.push(endDate);
    }

    query += ' ORDER BY ins_code, date';
    return db.prepare(query).all(...params);
  } catch (e) {
    console.error(e);
    return [];
  }
});

// Get order book snapshots
ipcMain.handle('get-orderbook', (event, { insCodes, startDate, endDate }) => {
  if (!db) return [];
  try {
    let query = 'SELECT * FROM order_book_snapshots WHERE 1=1';
    const params = [];

    if (insCodes && insCodes.length > 0) {
      query += ` AND ins_code IN (${insCodes.map(() => '?').join(',')})`;
      params.push(...insCodes);
    }

    if (startDate) {
      query += ' AND timestamp >= ?';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND timestamp <= ?';
      params.push(endDate);
    }

    query += ' ORDER BY ins_code, timestamp';
    return db.prepare(query).all(...params);
  } catch (e) {
    console.error(e);
    return [];
  }
});

// Get update logs
ipcMain.handle('get-update-logs', () => {
  if (!db) return [];
  try {
    return db.prepare('SELECT * FROM update_logs ORDER BY id DESC LIMIT 50').all();
  } catch (e) {
    console.error(e);
    return [];
  }
});

// Export to CSV
ipcMain.handle('export-csv', async (event, { data, filename }) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: filename || 'export.csv',
    filters: [{ name: 'CSV Files', extensions: ['csv'] }]
  });

  if (!result.canceled && result.filePath) {
    if (data.length === 0) {
      fs.writeFileSync(result.filePath, 'No data', 'utf-8');
      return { success: true, path: result.filePath };
    }

    const headers = Object.keys(data[0]);
    const csv = [
      headers.join(','),
      ...data.map(row => headers.map(h => {
        const val = row[h];
        if (val === null || val === undefined) return '';
        if (typeof val === 'string' && val.includes(',')) return `"${val}"`;
        return val;
      }).join(','))
    ].join('\n');

    fs.writeFileSync(result.filePath, '\ufeff' + csv, 'utf-8');
    return { success: true, path: result.filePath };
  }
  return { success: false };
});

// Export to Excel
ipcMain.handle('export-excel', async (event, { data, filename, sheetName }) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: filename || 'export.xlsx',
    filters: [{ name: 'Excel Files', extensions: ['xlsx'] }]
  });

  if (!result.canceled && result.filePath) {
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(data);
    XLSX.utils.book_append_sheet(wb, ws, sheetName || 'Data');
    XLSX.writeFile(wb, result.filePath);
    return { success: true, path: result.filePath };
  }
  return { success: false };
});

// Export multi-sheet Excel
ipcMain.handle('export-excel-multi', async (event, { sheets, filename }) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: filename || 'export.xlsx',
    filters: [{ name: 'Excel Files', extensions: ['xlsx'] }]
  });

  if (!result.canceled && result.filePath) {
    const wb = XLSX.utils.book_new();
    for (const sheet of sheets) {
      const ws = XLSX.utils.json_to_sheet(sheet.data);
      XLSX.utils.book_append_sheet(wb, ws, sheet.name);
    }
    XLSX.writeFile(wb, result.filePath);
    return { success: true, path: result.filePath };
  }
  return { success: false };
});

// ========== App Lifecycle ==========

app.whenReady().then(() => {
  initDatabase();
  createWindow();
});

app.on('window-all-closed', () => {
  if (db) db.close();
  app.quit();
});
