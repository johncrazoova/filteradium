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
  updateStats();
});

// ========== Load from Local DB ==========
async function loadStocks() {
  allStocks = await window.api.getStocks();
  renderSymbolList(allStocks);
}

async function loadSectors() {
  const sectors = await window.api.getSectors();
  const select = document.getElementById('sectorFilter');
  // Clear old options except first
  while (select.options.length > 1) select.remove(1);
  sectors.forEach(s => {
    if (s.sector) {
      const opt = document.createElement('option');
      opt.value = s.sector;
      opt.textContent = s.sector;
      select.appendChild(opt);
    }
  });
}

async function updateStats() {
  const stats = await window.api.getStats();
  document.getElementById('statStocks').textContent = stats.stocks;
  document.getElementById('statHistory').textContent = stats.history;
  document.getElementById('statClients').textContent = stats.clientType;
  document.getElementById('statShareholders').textContent = stats.shareholders;
}

// ========== Fetch from TSETMC ==========
async function fetchAllStocks() {
  const btn = document.getElementById('btnFetchStocks');
  btn.disabled = true;
  btn.innerHTML = '⏳ در حال دریافت...';

  try {
    const result = await window.api.fetchAllStocks();
    if (result.success) {
      alert(`✅ ${result.count} نماد دریافت شد`);
      await loadStocks();
      await loadSectors();
      await updateStats();
    } else {
      alert('❌ خطا: ' + result.error);
    }
  } catch (e) {
    alert('❌ خطا: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🔄 دریافت لیست نمادها';
  }
}

async function fetchStockHistory(insCode) {
  try {
    const result = await window.api.fetchHistory(insCode);
    return result;
  } catch (e) {
    return { success: false, error: e.message };
  }
}

async function fetchStockClientType(insCode) {
  try {
    return await window.api.fetchClientType(insCode);
  } catch (e) {
    return { success: false, error: e.message };
  }
}

async function fetchStockShareholders(insCode) {
  try {
    return await window.api.fetchShareholders(insCode);
  } catch (e) {
    return { success: false, error: e.message };
  }
}

// ========== UI ==========
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

  let filtered = stocks;
  if (searchTerm) {
    filtered = filtered.filter(s =>
      (s.symbol || '').toLowerCase().includes(searchTerm) ||
      (s.name || '').toLowerCase().includes(searchTerm)
    );
  }
  if (sectorFilter !== 'all') {
    filtered = filtered.filter(s => s.sector === sectorFilter);
  }

  filtered.forEach(stock => {
    const item = document.createElement('div');
    item.className = `symbol-item ${selectedStocks.includes(stock.ins_code) ? 'selected' : ''}`;
    item.innerHTML = `
      <input type="checkbox" ${selectedStocks.includes(stock.ins_code) ? 'checked' : ''}>
      <span class="symbol-name">${stock.symbol || '?'}</span>
      <span class="symbol-code">${stock.sector || ''}</span>
    `;
    item.onclick = () => toggleStock(stock.ins_code);
    container.appendChild(item);
  });
}

function toggleStock(insCode) {
  const idx = selectedStocks.indexOf(insCode);
  if (idx === -1) selectedStocks.push(insCode);
  else selectedStocks.splice(idx, 1);
  renderSymbolList(allStocks);
}

document.getElementById('symbolSearch').addEventListener('input', () => renderSymbolList(allStocks));
document.getElementById('sectorFilter').addEventListener('change', () => renderSymbolList(allStocks));

function getFilteredStocks() {
  const sector = document.getElementById('sectorFilter').value;
  let filtered = allStocks;
  if (sector !== 'all') filtered = filtered.filter(s => s.sector === sector);
  return filtered;
}

// ========== Fetch & Display Data ==========
async function fetchData() {
  const btn = document.getElementById('btnFetch');
  btn.disabled = true;
  btn.innerHTML = '⏳ دریافت...';

  try {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const insCodes = selectedStocks.length > 0 ? selectedStocks : getFilteredStocks().map(s => s.ins_code);

    if (insCodes.length === 0) {
      alert('لطفاً نمادی رو انتخاب کنید');
      return;
    }

    // First fetch history for selected stocks
    let fetched = 0;
    for (const code of insCodes) {
      document.getElementById('btnFetch').innerHTML = `⏳ ${++fetched}/${insCodes.length}`;
      await fetchStockHistory(code);
      if (currentDataType === 'client') await fetchStockClientType(code);
      if (currentDataType === 'shareholder') await fetchStockShareholders(code);
    }

    // Then query local DB
    const params = { insCodes, startDate, endDate };
    let data = [];

    switch (currentDataType) {
      case 'price':
        data = await window.api.getPriceHistory(params);
        break;
      case 'client':
        data = await window.api.getClientType(params);
        break;
      case 'shareholder':
        data = await window.api.getShareholders(params);
        break;
    }

    currentData = data;
    renderTable(data);
    document.getElementById('btnCSV').disabled = data.length === 0;
    document.getElementById('btnExcel').disabled = data.length === 0;
  } catch (e) {
    alert('❌ خطا: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🔄 دریافت و نمایش داده';
    await updateStats();
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

  const keys = Object.keys(data[0]);
  head.innerHTML = `<tr>${keys.map(k => `<th>${translateKey(k)}</th>`).join('')}</tr>`;

  const rows = data.slice(0, 2000).map(row => {
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

function translateKey(key) {
  const t = {
    'id': 'شناسه', 'ins_code': 'کد', 'symbol': 'نماد', 'date': 'تاریخ',
    'open': 'اولین', 'high': 'بیشترین', 'low': 'کمترین', 'close': 'پایانی',
    'last': 'آخرین', 'volume': 'حجم', 'value': 'ارزش', 'change': 'تغییر',
    'change_pct': 'تغییر%', 'name': 'نام', 'sector': 'صنعت',
    'individual_buy_count': 'تعداد خرید حقیقی', 'individual_sell_count': 'تعداد فروش حقیقی',
    'individual_buy_volume': 'حجم خرید حقیقی', 'individual_sell_volume': 'حجم فروش حقیقی',
    'corporate_buy_count': 'تعداد خرید حقوقی', 'corporate_sell_count': 'تعداد فروش حقوقی',
    'corporate_buy_volume': 'حجم خرید حقوقی', 'corporate_sell_volume': 'حجم فروش حقوقی',
    'data': 'داده سهامداران', 'updated_at': 'بروزرسانی'
  };
  return t[key] || key;
}

// ========== Export ==========
async function exportCSV() {
  if (currentData.length === 0) return;
  const names = { price: 'قیمت', client: 'حقیقی_حقوقی', shareholder: 'سهامداران' };
  const filename = `filteradium_${names[currentDataType]}_${new Date().toISOString().split('T')[0]}.csv`;
  const result = await window.api.exportCSV({ data: currentData, filename });
  if (result.success) alert(`✅ ذخیره شد:\n${result.path}`);
}

async function exportExcel() {
  if (currentData.length === 0) return;
  const names = { price: 'قیمت', client: 'حقیقی_حقوقی', shareholder: 'سهامداران' };
  const sheets = { price: 'Price', client: 'ClientType', shareholder: 'Shareholders' };
  const filename = `filteradium_${names[currentDataType]}_${new Date().toISOString().split('T')[0]}.xlsx`;
  const result = await window.api.exportExcel({ data: currentData, filename, sheetName: sheets[currentDataType] });
  if (result.success) alert(`✅ ذخیره شد:\n${result.path}`);
}
