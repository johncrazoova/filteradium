// ========== State ==========
let allStocks = [];
let selectedStocks = [];
let currentData = [];
let currentDataType = 'price';

// ========== Init ==========
document.addEventListener('DOMContentLoaded', async () => {
  await loadStocks();
  await loadSectors();
  setDefaultDates();
  setupRadioListeners();
});

// ========== Load Data ==========
async function loadStocks() {
  allStocks = await window.api.getStocks();
  renderSymbolList(allStocks);
}

async function loadSectors() {
  const sectors = await window.api.getSectors();
  const select = document.getElementById('sectorFilter');
  sectors.forEach(s => {
    if (s.sector) {
      const opt = document.createElement('option');
      opt.value = s.sector;
      opt.textContent = s.sector;
      select.appendChild(opt);
    }
  });
}

// ========== UI Setup ==========
function setDefaultDates() {
  const today = new Date();
  const yearAgo = new Date();
  yearAgo.setFullYear(yearAgo.getFullYear() - 1);

  document.getElementById('endDate').value = today.toISOString().split('T')[0];
  document.getElementById('startDate').value = yearAgo.toISOString().split('T')[0];
}

function setQuickDate(days) {
  const today = new Date();
  const past = new Date();
  past.setDate(past.getDate() - days);

  document.getElementById('endDate').value = today.toISOString().split('T')[0];
  document.getElementById('startDate').value = past.toISOString().split('T')[0];
}

function setupRadioListeners() {
  document.querySelectorAll('.radio-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.radio-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      item.querySelector('input').checked = true;
      currentDataType = item.dataset.type;
    });
  });
}

// ========== Symbol List ==========
function renderSymbolList(stocks) {
  const container = document.getElementById('symbolList');
  container.innerHTML = '';

  const searchTerm = document.getElementById('symbolSearch').value.toLowerCase();
  const sectorFilter = document.getElementById('sectorFilter').value;
  const marketFilter = document.getElementById('marketType').value;

  let filtered = stocks;

  if (searchTerm) {
    filtered = filtered.filter(s =>
      s.symbol.toLowerCase().includes(searchTerm) ||
      s.name.toLowerCase().includes(searchTerm)
    );
  }

  if (sectorFilter !== 'all') {
    filtered = filtered.filter(s => s.sector === sectorFilter);
  }

  if (marketFilter !== 'all') {
    filtered = filtered.filter(s => s.market_type == marketFilter);
  }

  filtered.forEach(stock => {
    const item = document.createElement('div');
    item.className = `symbol-item ${selectedStocks.includes(stock.ins_code) ? 'selected' : ''}`;
    item.innerHTML = `
      <input type="checkbox" ${selectedStocks.includes(stock.ins_code) ? 'checked' : ''}>
      <span class="symbol-name">${stock.symbol}</span>
      <span class="symbol-code">${stock.sector || ''}</span>
    `;
    item.onclick = () => toggleStock(stock.ins_code);
    container.appendChild(item);
  });
}

function toggleStock(insCode) {
  const idx = selectedStocks.indexOf(insCode);
  if (idx === -1) {
    selectedStocks.push(insCode);
  } else {
    selectedStocks.splice(idx, 1);
  }
  renderSymbolList(allStocks);
}

// Search filter
document.getElementById('symbolSearch').addEventListener('input', () => {
  renderSymbolList(allStocks);
});

// Sector filter
document.getElementById('sectorFilter').addEventListener('change', () => {
  renderSymbolList(allStocks);
});

// Market filter
document.getElementById('marketType').addEventListener('change', () => {
  renderSymbolList(allStocks);
});

// Select all / deselect all
function selectAll() {
  const filtered = getFilteredStocks();
  selectedStocks = filtered.map(s => s.ins_code);
  renderSymbolList(allStocks);
}

function deselectAll() {
  selectedStocks = [];
  renderSymbolList(allStocks);
}

function getFilteredStocks() {
  const sectorFilter = document.getElementById('sectorFilter').value;
  const marketFilter = document.getElementById('marketType').value;

  let filtered = allStocks;
  if (sectorFilter !== 'all') filtered = filtered.filter(s => s.sector === sectorFilter);
  if (marketFilter !== 'all') filtered = filtered.filter(s => s.market_type == marketFilter);
  return filtered;
}

// ========== Fetch Data ==========
async function fetchData() {
  const btn = document.getElementById('btnFetch');
  btn.disabled = true;
  btn.innerHTML = '<span class="btn-icon">⏳</span> در حال دریافت...';

  try {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const insCodes = selectedStocks.length > 0 ? selectedStocks : getFilteredStocks().map(s => s.ins_code);

    const params = { insCodes, startDate, endDate };

    let data = [];
    switch (currentDataType) {
      case 'price':
        data = await window.api.getPriceHistory(params);
        // Enrich with symbol names
        data = data.map(row => {
          const stock = allStocks.find(s => s.ins_code === row.ins_code);
          return { ...row, symbol: stock?.symbol || row.ins_code };
        });
        break;
      case 'client':
        data = await window.api.getClientType(params);
        data = data.map(row => {
          const stock = allStocks.find(s => s.ins_code === row.ins_code);
          return { ...row, symbol: stock?.symbol || row.ins_code };
        });
        break;
      case 'shareholder':
        data = await window.api.getShareholders(params);
        data = data.map(row => {
          const stock = allStocks.find(s => s.ins_code === row.ins_code);
          return { ...row, symbol: stock?.symbol || row.ins_code };
        });
        break;
      case 'orderbook':
        data = await window.api.getOrderBook(params);
        data = data.map(row => {
          const stock = allStocks.find(s => s.ins_code === row.ins_code);
          return { ...row, symbol: stock?.symbol || row.ins_code };
        });
        break;
    }

    currentData = data;
    renderTable(data);
    updateButtons(data.length > 0);
  } catch (e) {
    console.error(e);
    alert('خطا در دریافت داده: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">🔄</span> دریافت داده';
  }
}

// ========== Render Table ==========
function renderTable(data) {
  const head = document.getElementById('tableHead');
  const body = document.getElementById('tableBody');
  const empty = document.getElementById('emptyState');
  const count = document.getElementById('recordCount');

  if (data.length === 0) {
    head.innerHTML = '';
    body.innerHTML = '';
    empty.classList.remove('hidden');
    count.textContent = '0 رکورد';
    return;
  }

  empty.classList.add('hidden');
  count.textContent = `${data.length.toLocaleString('fa-IR')} رکورد`;

  // Headers
  const keys = Object.keys(data[0]);
  const headers = keys.map(k => `<th>${translateKey(k)}</th>`).join('');
  head.innerHTML = `<tr>${headers}</tr>`;

  // Rows (max 1000 for performance)
  const rows = data.slice(0, 1000).map(row => {
    const cells = keys.map(k => {
      const val = row[k];
      let cls = '';
      if (typeof val === 'number') {
        cls = 'num';
        if (k.includes('change') || k.includes('pct')) {
          cls += val > 0 ? ' positive' : val < 0 ? ' negative' : '';
        }
      }
      const display = val !== null && val !== undefined ?
        (typeof val === 'number' ? val.toLocaleString('fa-IR') : val) : '-';
      return `<td class="${cls}">${display}</td>`;
    }).join('');
    return `<tr>${cells}</tr>`;
  }).join('');

  body.innerHTML = rows;
}

// ========== Translation ==========
function translateKey(key) {
  const translations = {
    'id': 'شناسه',
    'ins_code': 'کد نماد',
    'symbol': 'نماد',
    'date': 'تاریخ',
    'open': 'اولین',
    'high': 'بیشترین',
    'low': 'کمترین',
    'close': 'پایانی',
    'last': 'آخرین',
    'volume': 'حجم',
    'value': 'ارزش',
    'change': 'تغییر',
    'change_pct': 'تغییر %',
    'trade_count': 'تعداد معامله',
    'individual_buy_count': 'تعداد خرید حقیقی',
    'individual_sell_count': 'تعداد فروش حقیقی',
    'individual_buy_volume': 'حجم خرید حقیقی',
    'individual_sell_volume': 'حجم فروش حقیقی',
    'corporate_buy_count': 'تعداد خرید حقوقی',
    'corporate_sell_count': 'تعداد فروش حقوقی',
    'corporate_buy_volume': '_volume خرید حقوقی',
    'corporate_sell_volume': 'حجم فروش حقوقی',
    'data': 'داده سهام‌داران',
    'timestamp': 'زمان',
    'total_demand': 'کل تقاضا',
    'total_supply': 'کل عرضه',
  };
  return translations[key] || key;
}

// ========== Export ==========
function updateButtons(enabled) {
  document.getElementById('btnCSV').disabled = !enabled;
  document.getElementById('btnExcel').disabled = !enabled;
  document.getElementById('btnExcelAll').disabled = !enabled;
}

async function exportCSV() {
  if (currentData.length === 0) return;

  const typeName = { price: 'قیمت', client: 'حقیقی_حقوقی', shareholder: 'سهامداران', orderbook: 'تابلو' };
  const filename = `filteradium_${typeName[currentDataType]}_${new Date().toISOString().split('T')[0]}.csv`;

  const result = await window.api.exportCSV({ data: currentData, filename });
  if (result.success) {
    alert(`فایل ذخیره شد:\n${result.path}`);
  }
}

async function exportExcel() {
  if (currentData.length === 0) return;

  const typeName = { price: 'قیمت', client: 'حقیقی_حقوقی', shareholder: 'سهامداران', orderbook: 'تابلو' };
  const sheetNames = { price: 'Price', client: 'ClientType', shareholder: 'Shareholders', orderbook: 'OrderBook' };
  const filename = `filteradium_${typeName[currentDataType]}_${new Date().toISOString().split('T')[0]}.xlsx`;

  const result = await window.api.exportExcel({
    data: currentData,
    filename,
    sheetName: sheetNames[currentDataType]
  });
  if (result.success) {
    alert(`فایل ذخیره شد:\n${result.path}`);
  }
}

async function exportExcelAll() {
  if (currentData.length === 0) return;

  const filename = `filteradium_all_${new Date().toISOString().split('T')[0]}.xlsx`;
  const sheets = [
    { name: 'Price', data: currentData }
  ];

  const result = await window.api.exportExcelMulti({ sheets, filename });
  if (result.success) {
    alert(`فایل ذخیره شد:\n${result.path}`);
  }
}
