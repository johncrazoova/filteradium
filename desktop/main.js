const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const Database = require('better-sqlite3');
const XLSX = require('xlsx');
const fs = require('fs');

let mainWindow;
let db;

function initDatabase() {
  const dbPath = path.join(app.getPath('userData'), 'filteradium.db');
  db = new Database(dbPath);
  db.exec(`
    CREATE TABLE IF NOT EXISTS stocks (
      ins_code INTEGER PRIMARY KEY, symbol TEXT, name TEXT, sector TEXT,
      market_type INTEGER, last_price REAL, close_price REAL, first_price REAL,
      yesterday_price REAL, high_price REAL, low_price REAL, volume REAL,
      value REAL, upper_limit REAL, lower_limit REAL, updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS price_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT, ins_code INTEGER, date TEXT,
      open REAL, high REAL, low REAL, close REAL, last REAL,
      volume REAL, value REAL, change REAL, change_pct REAL,
      UNIQUE(ins_code, date)
    );
    CREATE TABLE IF NOT EXISTS client_type (
      id INTEGER PRIMARY KEY AUTOINCREMENT, ins_code INTEGER, date TEXT,
      individual_buy_count INTEGER, individual_sell_count INTEGER,
      individual_buy_volume REAL, individual_sell_volume REAL,
      corporate_buy_count INTEGER, corporate_sell_count INTEGER,
      corporate_buy_volume REAL, corporate_sell_volume REAL,
      UNIQUE(ins_code, date)
    );
    CREATE TABLE IF NOT EXISTS shareholders (
      id INTEGER PRIMARY KEY AUTOINCREMENT, ins_code INTEGER, date TEXT,
      data TEXT, UNIQUE(ins_code, date)
    );
  `);
}

// ========== IPC Handlers ==========

ipcMain.handle('get-stocks', () => db.prepare('SELECT * FROM stocks ORDER BY symbol').all());
ipcMain.handle('get-sectors', () => db.prepare('SELECT DISTINCT sector FROM stocks WHERE sector IS NOT NULL ORDER BY sector').all());
ipcMain.handle('get-stats', () => ({
  stocks: db.prepare('SELECT COUNT(*) as c FROM stocks').get().c,
  history: db.prepare('SELECT COUNT(*) as c FROM price_history').get().c,
  clientType: db.prepare('SELECT COUNT(*) as c FROM client_type').get().c,
  shareholders: db.prepare('SELECT COUNT(*) as c FROM shareholders').get().c,
}));

// Save stocks from renderer (renderer fetches, main saves to DB)
ipcMain.handle('save-stocks', (event, stocks) => {
  const insert = db.prepare(`INSERT OR REPLACE INTO stocks
    (ins_code, symbol, name, sector, market_type, last_price, close_price,
     first_price, yesterday_price, high_price, low_price, volume, value,
     upper_limit, lower_limit, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`);
  
  const tx = db.transaction((list) => {
    for (const s of list) {
      insert.run(s.insCode, s.lVal18AFC, s.lVal18, s.cSecVal, s.flow,
        s.pDrCotVal, s.pClosing, s.priceFirst, s.priceYesterday,
        s.priceMax, s.priceMin, s.qTotTran5J, s.qTotCap, s.pMax, s.pMin);
    }
  });
  tx(stocks);
  return { success: true, count: stocks.length };
});

// Save price history from renderer
ipcMain.handle('save-price-history', (event, { insCode, data }) => {
  const ins = db.prepare(`INSERT OR REPLACE INTO price_history
    (ins_code, date, open, high, low, close, last, volume, value, change, change_pct)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`);
  
  const tx = db.transaction((items) => {
    for (const h of items) {
      const d = String(h.dEven);
      ins.run(insCode, `${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6,8)}`,
        h.priceFirst, h.priceMax, h.priceMin, h.pClosing, h.pDrCotVal,
        h.qTotTran5J, h.qTotCap, h.priceChange, 0);
    }
  });
  tx(data);
  return { success: true };
});

// Save client type from renderer
ipcMain.handle('save-client-type', (event, { insCode, data }) => {
  const today = new Date().toISOString().split('T')[0];
  db.prepare(`INSERT OR REPLACE INTO client_type
    (ins_code, date, individual_buy_count, individual_sell_count,
     individual_buy_volume, individual_sell_volume,
     corporate_buy_count, corporate_sell_count,
     corporate_buy_volume, corporate_sell_volume)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(
    insCode, today, data.buy_I_Count, data.sell_I_Count,
    data.buy_I_Volume, data.sell_I_Volume,
    data.buy_N_Count, data.sell_N_Count,
    data.buy_N_Volume, data.sell_N_Volume);
  return { success: true };
});

// Save shareholders from renderer
ipcMain.handle('save-shareholders', (event, { insCode, data }) => {
  const today = new Date().toISOString().split('T')[0];
  db.prepare(`INSERT OR REPLACE INTO shareholders (ins_code, date, data) VALUES (?, ?, ?)`)
    .run(insCode, today, JSON.stringify(data));
  return { success: true };
});

// Local DB queries
ipcMain.handle('get-price-history', (event, { insCodes, startDate, endDate }) => {
  let q = `SELECT ph.*, s.symbol FROM price_history ph LEFT JOIN stocks s ON ph.ins_code = s.ins_code WHERE 1=1`;
  const p = [];
  if (insCodes?.length) { q += ` AND ph.ins_code IN (${insCodes.map(()=>'?').join(',')})`; p.push(...insCodes); }
  if (startDate) { q += ' AND ph.date >= ?'; p.push(startDate); }
  if (endDate) { q += ' AND ph.date <= ?'; p.push(endDate); }
  return db.prepare(q + ' ORDER BY ph.ins_code, ph.date').all(...p);
});

ipcMain.handle('get-client-type-local', (event, { insCodes, startDate, endDate }) => {
  let q = `SELECT ct.*, s.symbol FROM client_type ct LEFT JOIN stocks s ON ct.ins_code = s.ins_code WHERE 1=1`;
  const p = [];
  if (insCodes?.length) { q += ` AND ct.ins_code IN (${insCodes.map(()=>'?').join(',')})`; p.push(...insCodes); }
  if (startDate) { q += ' AND ct.date >= ?'; p.push(startDate); }
  if (endDate) { q += ' AND ct.date <= ?'; p.push(endDate); }
  return db.prepare(q + ' ORDER BY ct.ins_code, ct.date').all(...p);
});

ipcMain.handle('get-shareholders-local', (event, { insCodes, startDate, endDate }) => {
  let q = `SELECT sh.*, s.symbol FROM shareholders sh LEFT JOIN stocks s ON sh.ins_code = s.ins_code WHERE 1=1`;
  const p = [];
  if (insCodes?.length) { q += ` AND sh.ins_code IN (${insCodes.map(()=>'?').join(',')})`; p.push(...insCodes); }
  if (startDate) { q += ' AND sh.date >= ?'; p.push(startDate); }
  if (endDate) { q += ' AND sh.date <= ?'; p.push(endDate); }
  return db.prepare(q).all(...p);
});

// Export
ipcMain.handle('export-csv', async (event, { data, filename }) => {
  const result = await dialog.showSaveDialog(mainWindow, { defaultPath: filename, filters: [{ name: 'CSV', extensions: ['csv'] }] });
  if (!result.canceled && result.filePath && data.length > 0) {
    const h = Object.keys(data[0]);
    const csv = [h.join(','), ...data.map(r => h.map(k => r[k] ?? '').join(','))].join('\n');
    fs.writeFileSync(result.filePath, '\ufeff' + csv, 'utf-8');
    return { success: true, path: result.filePath };
  }
  return { success: false };
});

ipcMain.handle('export-excel-multi', async (event, { sheets, filename }) => {
  const result = await dialog.showSaveDialog(mainWindow, { defaultPath: filename, filters: [{ name: 'Excel', extensions: ['xlsx'] }] });
  if (!result.canceled && result.filePath) {
    const wb = XLSX.utils.book_new();
    for (const s of sheets) { if (s.data.length) XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(s.data), s.name); }
    XLSX.writeFile(wb, result.filePath);
    return { success: true, path: result.filePath };
  }
  return { success: false };
});

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100, height: 750,
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false },
    title: 'FilteradiumExClient v1.3.0',
    backgroundColor: '#0B0B1A'
  });
  mainWindow.loadFile('index.html');
  mainWindow.setMenuBarVisibility(false);
}

app.whenReady().then(() => { initDatabase(); createWindow(); });
app.on('window-all-closed', () => { if (db) db.close(); app.quit(); });
