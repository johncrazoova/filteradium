const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const Database = require('better-sqlite3');
const XLSX = require('xlsx');
const https = require('https');
const http = require('http');
const fs = require('fs');

// Disable SSL verification for TSETMC
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

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

// ========== TSETMC API ==========
function httpGet(url) {
  return new Promise((resolve, reject) => {
    const isHttps = url.startsWith('https');
    const client = isHttps ? https : http;
    
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'fa-IR,fa;q=0.9',
        'Accept-Encoding': 'identity',
      },
      timeout: 60000,
    };
    
    if (isHttps) {
      options.rejectUnauthorized = false;
    }
    
    console.log('[HTTP] GET', url);
    
    const req = client.get(url, options, (res) => {
      console.log('[HTTP] Status:', res.statusCode);
      console.log('[HTTP] Headers:', JSON.stringify(res.headers).substring(0, 200));
      
      // Handle redirect
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        console.log('[HTTP] Redirect to:', res.headers.location);
        httpGet(res.headers.location).then(resolve).catch(reject);
        return;
      }
      
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log('[HTTP] Response length:', data.length);
        if (data.length > 0) {
          console.log('[HTTP] Preview:', data.substring(0, 150));
        }
        resolve({ status: res.statusCode, data, headers: res.headers });
      });
    });
    
    req.on('error', (e) => {
      console.log('[HTTP] Error:', e.message, e.code);
      reject(e);
    });
    
    req.on('timeout', () => {
      console.log('[HTTP] Timeout');
      req.destroy();
      reject(new Error('اتصال 60 ثانیه طول کشید'));
    });
  });
}

async function apiFetch(path) {
  const urls = [
    `https://cdn.tsetmc.com${path}`,
    `http://cdn.tsetmc.com${path}`,
    `https://tsetmc.com${path}`,
    `http://tsetmc.com${path}`,
  ];
  
  for (const url of urls) {
    try {
      console.log('[API] Trying:', url);
      const res = await httpGet(url);
      if (res.data && res.data.trim()) {
        const parsed = JSON.parse(res.data);
        console.log('[API] Success from:', url);
        return parsed;
      }
    } catch (e) {
      console.log('[API] Failed:', url, e.message);
    }
  }
  
  throw new Error('تمام سرورها در دسترس نیستند');
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

ipcMain.handle('test-connection', async () => {
  try {
    const data = await apiFetch('/api/MarketData/GetMarketState');
    return { success: true, data: 'اتصال برقرار است' };
  } catch (e) {
    return { success: false, error: e.message };
  }
});

ipcMain.handle('fetch-all-stocks', async () => {
  try {
    const data = await apiFetch('/api/ClosingPrice/GetMarketWatch/1/0');
    if (!data || !data.closingPriceAll) throw new Error('داده‌ای دریافت نشد');
    
    const insert = db.prepare(`INSERT OR REPLACE INTO stocks
      (ins_code, symbol, name, sector, market_type, last_price, close_price,
       first_price, yesterday_price, high_price, low_price, volume, value,
       upper_limit, lower_limit, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`);
    
    const tx = db.transaction((stocks) => {
      for (const s of stocks) {
        insert.run(s.insCode, s.lVal18AFC, s.lVal18, s.cSecVal, s.flow,
          s.pDrCotVal, s.pClosing, s.priceFirst, s.priceYesterday,
          s.priceMax, s.priceMin, s.qTotTran5J, s.qTotCap, s.pMax, s.pMin);
      }
    });
    tx(data.closingPriceAll);
    return { success: true, count: data.closingPriceAll.length };
  } catch (e) {
    return { success: false, error: e.message };
  }
});

ipcMain.handle('fetch-stock-data', async (event, { insCodes, types }) => {
  const fetched = { price: 0, client: 0, shareholder: 0 };
  
  for (let i = 0; i < insCodes.length; i++) {
    const code = insCodes[i];
    
    if (types.includes('price')) {
      try {
        const data = await apiFetch(`/api/ClosingPrice/GetClosingPriceHistory/${code}`);
        if (data && data.closingPriceHistory) {
          const ins = db.prepare(`INSERT OR REPLACE INTO price_history
            (ins_code, date, open, high, low, close, last, volume, value, change, change_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`);
          for (const h of data.closingPriceHistory) {
            const d = String(h.dEven);
            ins.run(code, `${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6,8)}`,
              h.priceFirst, h.priceMax, h.priceMin, h.pClosing, h.pDrCotVal,
              h.qTotTran5J, h.qTotCap, h.priceChange, 0);
          }
          fetched.price++;
        }
      } catch (e) { console.log('Price error:', e.message); }
    }
    
    if (types.includes('client')) {
      try {
        const data = await apiFetch(`/api/ClientType/GetClientType/${code}/0`);
        if (data) {
          const today = new Date().toISOString().split('T')[0];
          db.prepare(`INSERT OR REPLACE INTO client_type
            (ins_code, date, individual_buy_count, individual_sell_count,
             individual_buy_volume, individual_sell_volume,
             corporate_buy_count, corporate_sell_count,
             corporate_buy_volume, corporate_sell_volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(
            code, today, data.buy_I_Count, data.sell_I_Count,
            data.buy_I_Volume, data.sell_I_Volume,
            data.buy_N_Count, data.sell_N_Count,
            data.buy_N_Volume, data.sell_N_Volume);
          fetched.client++;
        }
      } catch (e) { console.log('Client error:', e.message); }
    }
    
    if (types.includes('shareholder')) {
      try {
        const data = await apiFetch(`/api/Shareholder/GetInstrumentShareholders/${code}`);
        if (data) {
          const today = new Date().toISOString().split('T')[0];
          db.prepare(`INSERT OR REPLACE INTO shareholders (ins_code, date, data) VALUES (?, ?, ?)`)
            .run(code, today, JSON.stringify(data));
          fetched.shareholder++;
        }
      } catch (e) { console.log('Shareholder error:', e.message); }
    }
    
    if (mainWindow) mainWindow.webContents.send('fetch-progress', { current: i + 1, total: insCodes.length });
    await new Promise(r => setTimeout(r, 200));
  }
  
  return { success: true, fetched };
});

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

ipcMain.handle('export-csv', async (event, { data, filename }) => {
  const result = await dialog.showSaveDialog(mainWindow, { defaultPath: filename, filters: [{ name: 'CSV', extensions: ['csv'] }] });
  if (!result.canceled && result.filePath && data.length > 0) {
    const h = Object.keys(data[0]);
    const csv = [h.join(','), ...data.map(r => h.map(k => { const v = r[k]; return v == null ? '' : v; }).join(','))].join('\n');
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
    title: 'FilteradiumExClient v1.2.0',
    backgroundColor: '#0B0B1A'
  });
  mainWindow.loadFile('index.html');
  mainWindow.setMenuBarVisibility(false);
}

app.whenReady().then(() => { initDatabase(); createWindow(); });
app.on('window-all-closed', () => { if (db) db.close(); app.quit(); });
