const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const Database = require('better-sqlite3');
const XLSX = require('xlsx');
const https = require('https');
const http = require('http');
const fs = require('fs');

let mainWindow;
let db;

// ========== Database Init ==========
function initDatabase() {
  const dbPath = path.join(app.getPath('userData'), 'filteradium.db');
  db = new Database(dbPath);

  db.exec(`
    CREATE TABLE IF NOT EXISTS stocks (
      ins_code INTEGER PRIMARY KEY,
      symbol TEXT,
      name TEXT,
      sector TEXT,
      market_type INTEGER,
      last_price REAL,
      close_price REAL,
      first_price REAL,
      yesterday_price REAL,
      high_price REAL,
      low_price REAL,
      volume REAL,
      value REAL,
      upper_limit REAL,
      lower_limit REAL,
      updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS price_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ins_code INTEGER,
      date TEXT,
      open REAL,
      high REAL,
      low REAL,
      close REAL,
      last REAL,
      volume REAL,
      value REAL,
      change REAL,
      change_pct REAL,
      UNIQUE(ins_code, date)
    );

    CREATE TABLE IF NOT EXISTS client_type (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ins_code INTEGER,
      date TEXT,
      individual_buy_count INTEGER,
      individual_sell_count INTEGER,
      individual_buy_volume REAL,
      individual_sell_volume REAL,
      corporate_buy_count INTEGER,
      corporate_sell_count INTEGER,
      corporate_buy_volume REAL,
      corporate_sell_volume REAL,
      UNIQUE(ins_code, date)
    );

    CREATE TABLE IF NOT EXISTS shareholders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ins_code INTEGER,
      date TEXT,
      data TEXT,
      UNIQUE(ins_code, date)
    );

    CREATE TABLE IF NOT EXISTS update_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp TEXT,
      update_type TEXT,
      stocks_count INTEGER,
      status TEXT
    );
  `);

  console.log('Database initialized:', dbPath);
}

// ========== TSETMC API Client ==========
const TSETMC = {
  BASE: 'https://cdn.tsetmc.com',
  HEADERS: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://old.tsetmc.com/',
    'Origin': 'https://old.tsetmc.com'
  },

  async fetch(url) {
    return new Promise((resolve, reject) => {
      const client = url.startsWith('https') ? https : http;
      const req = client.get(url, { headers: this.HEADERS, timeout: 30000 }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(e);
          }
        });
      });
      req.on('error', reject);
      req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
    });
  },

  // Get all stocks
  async getAllStocks() {
    return this.fetch(`${this.BASE}/api/ClosingPrice/GetMarketWatch/1/0`);
  },

  // Get stock history
  async getHistory(insCode) {
    return this.fetch(`${this.BASE}/api/ClosingPrice/GetClosingPriceHistory/${insCode}`);
  },

  // Get client type
  async getClientType(insCode) {
    return this.fetch(`${this.BASE}/api/ClientType/GetClientType/${insCode}/0`);
  },

  // Get shareholders
  async getShareholders(insCode) {
    return this.fetch(`${this.BASE}/api/Shareholder/GetInstrumentShareholders/${insCode}`);
  },

  // Search instruments
  async search(term) {
    return this.fetch(`${this.BASE}/api/Instrument/GetInstrumentSearch/${term}`);
  }
};

// ========== IPC Handlers ==========

// Get all stocks from local DB
ipcMain.handle('get-stocks', () => {
  return db.prepare('SELECT * FROM stocks ORDER BY symbol').all();
});

// Get sectors
ipcMain.handle('get-sectors', () => {
  return db.prepare('SELECT DISTINCT sector FROM stocks WHERE sector IS NOT NULL ORDER BY sector').all();
});

// Fetch all stocks from TSETMC
ipcMain.handle('fetch-all-stocks', async () => {
  try {
    const data = await TSETMC.getAllStocks();
    if (!data || !data.closingPriceAll) {
      throw new Error('No data received');
    }

    const insert = db.prepare(`
      INSERT OR REPLACE INTO stocks (ins_code, symbol, name, sector, market_type,
        last_price, close_price, first_price, yesterday_price, high_price, low_price,
        volume, value, upper_limit, lower_limit, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    `);

    const transaction = db.transaction((stocks) => {
      for (const s of stocks) {
        insert.run(
          s.insCode, s.lVal18AFC, s.lVal18, s.cSecVal, s.flow,
          s.pDrCotVal, s.pClosing, s.priceFirst, s.priceYesterday,
          s.priceMax, s.priceMin, s.qTotTran5J, s.qTotCap,
          s.pMax, s.pMin
        );
      }
    });

    transaction(data.closingPriceAll);

    db.prepare(`INSERT INTO update_log (timestamp, update_type, stocks_count, status)
      VALUES (datetime('now'), 'stocks', ?, 'success')`).run(data.closingPriceAll.length);

    return { success: true, count: data.closingPriceAll.length };
  } catch (e) {
    return { success: false, error: e.message };
  }
});

// Fetch history for a stock
ipcMain.handle('fetch-history', async (event, insCode) => {
  try {
    const data = await TSETMC.getHistory(insCode);
    if (!data || !data.closingPriceHistory) {
      throw new Error('No history data');
    }

    const insert = db.prepare(`
      INSERT OR REPLACE INTO price_history (ins_code, date, open, high, low, close, last, volume, value, change, change_pct)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const transaction = db.transaction((items) => {
      for (const h of items) {
        const dateStr = String(h.dEven);
        const date = `${dateStr.slice(0,4)}-${dateStr.slice(4,6)}-${dateStr.slice(6,8)}`;
        insert.run(
          insCode, date, h.priceFirst, h.priceMax, h.priceMin,
          h.pClosing, h.pDrCotVal, h.qTotTran5J, h.qTotCap,
          h.priceChange, 0
        );
      }
    });

    transaction(data.closingPriceHistory);
    return { success: true, count: data.closingPriceHistory.length };
  } catch (e) {
    return { success: false, error: e.message };
  }
});

// Fetch client type for a stock
ipcMain.handle('fetch-client-type', async (event, insCode) => {
  try {
    const data = await TSETMC.getClientType(insCode);
    if (!data) throw new Error('No data');

    const today = new Date().toISOString().split('T')[0];
    db.prepare(`INSERT OR REPLACE INTO client_type
      (ins_code, date, individual_buy_count, individual_sell_count,
       individual_buy_volume, individual_sell_volume,
       corporate_buy_count, corporate_sell_count,
       corporate_buy_volume, corporate_sell_volume)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(
      insCode, today,
      data.buy_I_Count, data.sell_I_Count,
      data.buy_I_Volume, data.sell_I_Volume,
      data.buy_N_Count, data.sell_N_Count,
      data.buy_N_Volume, data.sell_N_Volume
    );

    return { success: true };
  } catch (e) {
    return { success: false, error: e.message };
  }
});

// Fetch shareholders for a stock
ipcMain.handle('fetch-shareholders', async (event, insCode) => {
  try {
    const data = await TSETMC.getShareholders(insCode);
    if (!data) throw new Error('No data');

    const today = new Date().toISOString().split('T')[0];
    db.prepare(`INSERT OR REPLACE INTO shareholders (ins_code, date, data)
      VALUES (?, ?, ?)`).run(insCode, today, JSON.stringify(data));

    return { success: true };
  } catch (e) {
    return { success: false, error: e.message };
  }
});

// Get price history from local DB
ipcMain.handle('get-price-history', (event, { insCodes, startDate, endDate }) => {
  let query = `SELECT ph.*, s.symbol FROM price_history ph
    LEFT JOIN stocks s ON ph.ins_code = s.ins_code WHERE 1=1`;
  const params = [];

  if (insCodes && insCodes.length > 0) {
    query += ` AND ph.ins_code IN (${insCodes.map(() => '?').join(',')})`;
    params.push(...insCodes);
  }
  if (startDate) { query += ' AND ph.date >= ?'; params.push(startDate); }
  if (endDate) { query += ' AND ph.date <= ?'; params.push(endDate); }

  query += ' ORDER BY ph.ins_code, ph.date';
  return db.prepare(query).all(...params);
});

// Get client type from local DB
ipcMain.handle('get-client-type-local', (event, { insCodes, startDate, endDate }) => {
  let query = `SELECT ct.*, s.symbol FROM client_type ct
    LEFT JOIN stocks s ON ct.ins_code = s.ins_code WHERE 1=1`;
  const params = [];

  if (insCodes && insCodes.length > 0) {
    query += ` AND ct.ins_code IN (${insCodes.map(() => '?').join(',')})`;
    params.push(...insCodes);
  }
  if (startDate) { query += ' AND ct.date >= ?'; params.push(startDate); }
  if (endDate) { query += ' AND ct.date <= ?'; params.push(endDate); }

  query += ' ORDER BY ct.ins_code, ct.date';
  return db.prepare(query).all(...params);
});

// Get shareholders from local DB
ipcMain.handle('get-shareholders-local', (event, { insCodes, startDate, endDate }) => {
  let query = `SELECT sh.*, s.symbol FROM shareholders sh
    LEFT JOIN stocks s ON sh.ins_code = s.ins_code WHERE 1=1`;
  const params = [];

  if (insCodes && insCodes.length > 0) {
    query += ` AND sh.ins_code IN (${insCodes.map(() => '?').join(',')})`;
    params.push(...insCodes);
  }
  if (startDate) { query += ' AND sh.date >= ?'; params.push(startDate); }
  if (endDate) { query += ' AND sh.date <= ?'; params.push(endDate); }

  return db.prepare(query).all(...params);
});

// Get update log
ipcMain.handle('get-update-log', () => {
  return db.prepare('SELECT * FROM update_log ORDER BY id DESC LIMIT 20').all();
});

// Get DB stats
ipcMain.handle('get-stats', () => {
  return {
    stocks: db.prepare('SELECT COUNT(*) as count FROM stocks').get().count,
    history: db.prepare('SELECT COUNT(*) as count FROM price_history').get().count,
    clientType: db.prepare('SELECT COUNT(*) as count FROM client_type').get().count,
    shareholders: db.prepare('SELECT COUNT(*) as count FROM shareholders').get().count,
  };
});

// Export CSV
ipcMain.handle('export-csv', async (event, { data, filename }) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: filename || 'export.csv',
    filters: [{ name: 'CSV', extensions: ['csv'] }]
  });

  if (!result.canceled && result.filePath && data.length > 0) {
    const headers = Object.keys(data[0]);
    const csv = [
      headers.join(','),
      ...data.map(row => headers.map(h => {
        const val = row[h];
        if (val === null || val === undefined) return '';
        if (typeof val === 'string' && (val.includes(',') || val.includes('"')))
          return `"${val.replace(/"/g, '""')}"`;
        return val;
      }).join(','))
    ].join('\n');

    fs.writeFileSync(result.filePath, '\ufeff' + csv, 'utf-8');
    return { success: true, path: result.filePath };
  }
  return { success: false };
});

// Export Excel
ipcMain.handle('export-excel', async (event, { data, filename, sheetName }) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: filename || 'export.xlsx',
    filters: [{ name: 'Excel', extensions: ['xlsx'] }]
  });

  if (!result.canceled && result.filePath && data.length > 0) {
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(data);
    XLSX.utils.book_append_sheet(wb, ws, sheetName || 'Data');
    XLSX.writeFile(wb, result.filePath);
    return { success: true, path: result.filePath };
  }
  return { success: false };
});

// ========== Window ==========
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 750,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    title: 'Filteradium',
    backgroundColor: '#0B0B1A'
  });

  mainWindow.loadFile('index.html');
  mainWindow.setMenuBarVisibility(false);
}

app.whenReady().then(() => {
  initDatabase();
  createWindow();
});

app.on('window-all-closed', () => {
  if (db) db.close();
  app.quit();
});
