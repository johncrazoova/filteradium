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
}

// ========== TSETMC API Client ==========
const TSETMC = {
  BASE: 'https://cdn.tsetmc.com',
  BASE_HTTP: 'http://cdn.tsetmc.com',
  HEADERS: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8',
    'Referer': 'https://old.tsetmc.com/',
    'Origin': 'https://old.tsetmc.com'
  },

  async fetchWithFallback(path) {
    // Try HTTPS first, then HTTP
    try {
      return await this._fetch(this.BASE + path);
    } catch (e) {
      console.log('HTTPS failed, trying HTTP...');
      return await this._fetch(this.BASE_HTTP + path);
    }
  },

  _fetch(url) {
    return new Promise((resolve, reject) => {
      const client = url.startsWith('https') ? https : http;
      console.log('Fetching:', url);
      const req = client.get(url, { headers: this.HEADERS, timeout: 30000 }, (res) => {
        console.log('Response status:', res.statusCode);
        console.log('Response headers:', JSON.stringify(res.headers));
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          console.log('Response length:', data.length);
          console.log('Response preview:', data.substring(0, 200));
          if (!data || data.trim() === '') {
            reject(new Error(`پاسخ خالی از سرور (status: ${res.statusCode})`));
            return;
          }
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(new Error(`خطا در پردازش JSON: ${data.substring(0, 100)}`));
          }
        });
      });
      req.on('error', (e) => {
        reject(new Error(`خطای شبکه: ${e.message}`));
      });
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('زمان اتصال تمام شد (30 ثانیه)'));
      });
    });
  },

  async getAllStocks() {
    return this.fetchWithFallback('/api/ClosingPrice/GetMarketWatch/1/0');
  },

  // Test connection
  async testConnection() {
    try {
      const data = await this.fetchWithFallback('/api/MarketData/GetMarketState');
      return { success: true, data };
    } catch (e) {
      return { success: false, error: e.message };
    }
  },

  async getHistory(insCode) {
    return this.fetchWithFallback(`/api/ClosingPrice/GetClosingPriceHistory/${insCode}`);
  },

  async getClientType(insCode) {
    return this.fetchWithFallback(`/api/ClientType/GetClientType/${insCode}/0`);
  },

  async getShareholders(insCode) {
    return this.fetchWithFallback(`/api/Shareholder/GetInstrumentShareholders/${insCode}`);
  }
};

// ========== IPC Handlers ==========

ipcMain.handle('get-stocks', () => {
  return db.prepare('SELECT * FROM stocks ORDER BY symbol').all();
});

ipcMain.handle('get-sectors', () => {
  return db.prepare('SELECT DISTINCT sector FROM stocks WHERE sector IS NOT NULL ORDER BY sector').all();
});

ipcMain.handle('get-stats', () => {
  return {
    stocks: db.prepare('SELECT COUNT(*) as c FROM stocks').get().c,
    history: db.prepare('SELECT COUNT(*) as c FROM price_history').get().c,
    clientType: db.prepare('SELECT COUNT(*) as c FROM client_type').get().c,
    shareholders: db.prepare('SELECT COUNT(*) as c FROM shareholders').get().c,
  };
});

// Test connection
ipcMain.handle('test-connection', async () => {
  try {
    const result = await TSETMC.testConnection();
    return result;
  } catch (e) {
    return { success: false, error: e.message };
  }
});

// Fetch all stocks from TSETMC
ipcMain.handle('fetch-all-stocks', async () => {
  try {
    const data = await TSETMC.getAllStocks();
    if (!data || !data.closingPriceAll) {
      throw new Error('داده‌ای دریافت نشد');
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

// Fetch data for selected stocks (supports multiple types)
ipcMain.handle('fetch-stock-data', async (event, { insCodes, types }) => {
  let fetched = { price: 0, client: 0, shareholder: 0 };
  const total = insCodes.length;

  for (let i = 0; i < insCodes.length; i++) {
    const insCode = insCodes[i];

    if (types.includes('price')) {
      try {
        const data = await TSETMC.getHistory(insCode);
        if (data && data.closingPriceHistory) {
          const insert = db.prepare(`INSERT OR REPLACE INTO price_history
            (ins_code, date, open, high, low, close, last, volume, value, change, change_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`);
          for (const h of data.closingPriceHistory) {
            const d = String(h.dEven);
            insert.run(insCode, `${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6,8)}`,
              h.priceFirst, h.priceMax, h.priceMin, h.pClosing, h.pDrCotVal,
              h.qTotTran5J, h.qTotCap, h.priceChange, 0);
          }
          fetched.price++;
        }
      } catch (e) { console.error('Price error:', e.message); }
    }

    if (types.includes('client')) {
      try {
        const data = await TSETMC.getClientType(insCode);
        if (data) {
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
            data.buy_N_Volume, data.sell_N_Volume
          );
          fetched.client++;
        }
      } catch (e) { console.error('Client error:', e.message); }
    }

    if (types.includes('shareholder')) {
      try {
        const data = await TSETMC.getShareholders(insCode);
        if (data) {
          const today = new Date().toISOString().split('T')[0];
          db.prepare(`INSERT OR REPLACE INTO shareholders (ins_code, date, data)
            VALUES (?, ?, ?)`).run(insCode, today, JSON.stringify(data));
          fetched.shareholder++;
        }
      } catch (e) { console.error('Shareholder error:', e.message); }
    }

    // Progress callback
    if (mainWindow) {
      mainWindow.webContents.send('fetch-progress', { current: i + 1, total });
    }

    // Rate limit
    await new Promise(r => setTimeout(r, 100));
  }

  return { success: true, fetched };
});

// Local DB queries
ipcMain.handle('get-price-history', (event, { insCodes, startDate, endDate }) => {
  let q = `SELECT ph.*, s.symbol FROM price_history ph LEFT JOIN stocks s ON ph.ins_code = s.ins_code WHERE 1=1`;
  const p = [];
  if (insCodes && insCodes.length) { q += ` AND ph.ins_code IN (${insCodes.map(()=>'?').join(',')})`; p.push(...insCodes); }
  if (startDate) { q += ' AND ph.date >= ?'; p.push(startDate); }
  if (endDate) { q += ' AND ph.date <= ?'; p.push(endDate); }
  return db.prepare(q + ' ORDER BY ph.ins_code, ph.date').all(...p);
});

ipcMain.handle('get-client-type-local', (event, { insCodes, startDate, endDate }) => {
  let q = `SELECT ct.*, s.symbol FROM client_type ct LEFT JOIN stocks s ON ct.ins_code = s.ins_code WHERE 1=1`;
  const p = [];
  if (insCodes && insCodes.length) { q += ` AND ct.ins_code IN (${insCodes.map(()=>'?').join(',')})`; p.push(...insCodes); }
  if (startDate) { q += ' AND ct.date >= ?'; p.push(startDate); }
  if (endDate) { q += ' AND ct.date <= ?'; p.push(endDate); }
  return db.prepare(q + ' ORDER BY ct.ins_code, ct.date').all(...p);
});

ipcMain.handle('get-shareholders-local', (event, { insCodes, startDate, endDate }) => {
  let q = `SELECT sh.*, s.symbol FROM shareholders sh LEFT JOIN stocks s ON sh.ins_code = s.ins_code WHERE 1=1`;
  const p = [];
  if (insCodes && insCodes.length) { q += ` AND sh.ins_code IN (${insCodes.map(()=>'?').join(',')})`; p.push(...insCodes); }
  if (startDate) { q += ' AND sh.date >= ?'; p.push(startDate); }
  if (endDate) { q += ' AND sh.date <= ?'; p.push(endDate); }
  return db.prepare(q).all(...p);
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
        const v = row[h];
        if (v === null || v === undefined) return '';
        if (typeof v === 'string' && (v.includes(',') || v.includes('"')))
          return `"${v.replace(/"/g, '""')}"`;
        return v;
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

// Export multi-sheet Excel
ipcMain.handle('export-excel-multi', async (event, { sheets, filename }) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: filename || 'export.xlsx',
    filters: [{ name: 'Excel', extensions: ['xlsx'] }]
  });
  if (!result.canceled && result.filePath) {
    const wb = XLSX.utils.book_new();
    for (const sheet of sheets) {
      if (sheet.data.length > 0) {
        const ws = XLSX.utils.json_to_sheet(sheet.data);
        XLSX.utils.book_append_sheet(wb, ws, sheet.name);
      }
    }
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
    title: 'FilteradiumExClient',
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
