let allStocks = [];
let selectedStocks = [];
let allData = {}; // { price: [...], client: [...], shareholder: [...] }

document.addEventListener('DOMContentLoaded', async () => {
  await loadStocks();
  await loadSectors();
  setDefaultDates();
  updateStats();
  window.api.onProgress(updateProgress);
});

async function loadStocks() {
  allStocks = await window.api.getStocks();
  renderSymbolList(allStocks);
}

async function loadSectors() {
  const sectors = await window.api.getSectors();
  const sel = document.getElementById('sectorFilter');
  while (sel.options.length > 1) sel.remove(1);
  sectors.forEach(s => {
    if (s.sector) {
      const o = document.createElement('option');
      o.value = s.sector;
      o.textContent = s.sector;
      sel.appendChild(o);
    }
  });
}

async function updateStats() {
  const s = await window.api.getStats();
  document.getElementById('statStocks').textContent = s.stocks;
  document.getElementById('statHistory').textContent = s.history;
  document.getElementById('statClients').textContent = s.clientType;
  document.getElementById('statShareholders').textContent = s.shareholders;
}

// ========== Fetch from TSETMC ==========
async function fetchAllStocks() {
  const btn = document.getElementById('btnFetchStocks');
  btn.disabled = true;
  btn.innerHTML = '⏳ دریافت...';
  try {
    const r = await window.api.fetchAllStocks();
    if (r.success) {
      alert(`✅ ${r.count} نماد دریافت شد`);
      await loadStocks();
      await loadSectors();
      await updateStats();
    } else {
      alert('❌ ' + r.error);
    }
  } catch (e) { alert('❌ ' + e.message); }
  finally { btn.disabled = false; btn.innerHTML = '🔄 دریافت لیست نمادها از TSETMC'; }
}

async function fetchData() {
  const btn = document.getElementById('btnFetch');
  btn.disabled = true;

  const types = getSelectedTypes();
  if (types.length === 0) {
    alert('لطفاً حداقل یک نوع داده انتخاب کنید');
    btn.disabled = false;
    return;
  }

  const insCodes = selectedStocks.length > 0 ? selectedStocks : getFilteredStocks().map(s => s.ins_code);
  if (insCodes.length === 0) {
    alert('لطفاً نمادی رو انتخاب کنید');
    btn.disabled = false;
    return;
  }

  btn.innerHTML = `⏳ 0/${insCodes.length}`;

  try {
    const r = await window.api.fetchStockData({ insCodes, types });
    if (r.success) {
      let msg = '✅ دریافت شد:\n';
      if (types.includes('price')) msg += `  📈 قیمت: ${r.fetched.price} نماد\n`;
      if (types.includes('client')) msg += `  👥 حقیقی/حقوقی: ${r.fetched.client} نماد\n`;
      if (types.includes('shareholder')) msg += `  🏢 سهامداران: ${r.fetched.shareholder} نماد`;
      alert(msg);
    } else {
      alert('❌ ' + r.error);
    }
  } catch (e) { alert('❌ ' + e.message); }
  finally {
    btn.disabled = false;
    btn.innerHTML = '🔄 دریافت و ذخیره داده';
    await loadStocks();
    await updateStats();
  }
}

function updateProgress({ current, total }) {
  const btn = document.getElementById('btnFetch');
  btn.innerHTML = `⏳ ${current}/${total}`;
}

function getSelectedTypes() {
  const types = [];
  document.querySelectorAll('.type-check:checked').forEach(cb => types.push(cb.value));
  return types;
}

// ========== Display Data ==========
async function displayData() {
  const startDate = document.getElementById('startDate').value;
  const endDate = document.getElementById('endDate').value;
  const insCodes = selectedStocks.length > 0 ? selectedStocks : getFilteredStocks().map(s => s.ins_code);
  const types = getSelectedTypes();

  if (insCodes.length === 0) { alert('نمادی انتخاب نشده'); return; }
  if (types.length === 0) { alert('نوع داده‌ای انتخاب نشده'); return; }

  const params = { insCodes, startDate, endDate };
  allData = {};

  if (types.includes('price')) allData.price = await window.api.getPriceHistory(params);
  if (types.includes('client')) allData.client = await window.api.getClientType(params);
  if (types.includes('shareholder')) allData.shareholder = await window.api.getShareholders(params);

  // Show first available type
  if (allData.price && allData.price.length > 0) renderTable(allData.price, 'price');
  else if (allData.client && allData.client.length > 0) renderTable(allData.client, 'client');
  else if (allData.shareholder && allData.shareholder.length > 0) renderTable(allData.shareholder, 'shareholder');
  else {
    renderTable([], '');
    alert('داده‌ای یافت نشد. ابتدا داده رو دریافت کنید.');
  }
}

function switchTab(type) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`[data-tab="${type}"]`).classList.add('active');
  if (allData[type]) renderTable(allData[type], type);
}

function renderTable(data, type) {
  const head = document.getElementById('tableHead');
  const body = document.getElementById('tableBody');
  const empty = document.getElementById('emptyState');
  const count = document.getElementById('recordCount');

  // Show/hide tabs
  document.querySelectorAll('.tab-btn').forEach(b => {
    const t = b.dataset.tab;
    b.style.display = allData[t] && allData[t].length > 0 ? '' : 'none';
  });

  if (!data || data.length === 0) {
    head.innerHTML = ''; body.innerHTML = '';
    empty.classList.remove('hidden');
    count.textContent = '0 رکورد';
    return;
  }

  empty.classList.add('hidden');
  count.textContent = `${data.length.toLocaleString('fa-IR')} رکورد`;

  const keys = Object.keys(data[0]);
  head.innerHTML = `<tr>${keys.map(k => `<th>${T(k)}</th>`).join('')}</tr>`;

  body.innerHTML = data.slice(0, 3000).map(row => {
    return '<tr>' + keys.map(k => {
      const v = row[k];
      let c = typeof v === 'number' ? 'num' : '';
      if (k.includes('change') || k.includes('pct')) c += v > 0 ? ' positive' : v < 0 ? ' negative' : '';
      const d = v !== null && v !== undefined ? (typeof v === 'number' ? v.toLocaleString('fa-IR') : v) : '-';
      return `<td class="${c}">${d}</td>`;
    }).join('') + '</tr>';
  }).join('');
}

function T(k) {
  const m = {
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
  return m[k] || k;
}

// ========== UI ==========
function setDefaultDates() {
  const t = new Date(), y = new Date();
  y.setFullYear(y.getFullYear() - 1);
  document.getElementById('endDate').value = t.toISOString().split('T')[0];
  document.getElementById('startDate').value = y.toISOString().split('T')[0];
}

function setQuickDate(d) {
  const t = new Date(), p = new Date();
  p.setDate(p.getDate() - d);
  document.getElementById('endDate').value = t.toISOString().split('T')[0];
  document.getElementById('startDate').value = p.toISOString().split('T')[0];
}

function renderSymbolList(stocks) {
  const c = document.getElementById('symbolList');
  c.innerHTML = '';
  const q = document.getElementById('symbolSearch').value.toLowerCase();
  const sec = document.getElementById('sectorFilter').value;
  let f = stocks;
  if (q) f = f.filter(s => (s.symbol||'').toLowerCase().includes(q) || (s.name||'').toLowerCase().includes(q));
  if (sec !== 'all') f = f.filter(s => s.sector === sec);
  f.forEach(s => {
    const d = document.createElement('div');
    d.className = `symbol-item ${selectedStocks.includes(s.ins_code) ? 'selected' : ''}`;
    d.innerHTML = `<input type="checkbox" ${selectedStocks.includes(s.ins_code) ? 'checked' : ''}>
      <span class="symbol-name">${s.symbol||'?'}</span>
      <span class="symbol-code">${s.sector||''}</span>`;
    d.onclick = () => { toggle(s.ins_code); };
    c.appendChild(d);
  });
}

function toggle(code) {
  const i = selectedStocks.indexOf(code);
  if (i === -1) selectedStocks.push(code); else selectedStocks.splice(i, 1);
  renderSymbolList(allStocks);
}

function getFilteredStocks() {
  const sec = document.getElementById('sectorFilter').value;
  let f = allStocks;
  if (sec !== 'all') f = f.filter(s => s.sector === sec);
  return f;
}

document.getElementById('symbolSearch').addEventListener('input', () => renderSymbolList(allStocks));
document.getElementById('sectorFilter').addEventListener('change', () => renderSymbolList(allStocks));

// ========== Export ==========
async function exportCSV() {
  const types = getSelectedTypes();
  const sheets = [];
  if (allData.price && allData.price.length) sheets.push({ name: 'Price', data: allData.price });
  if (allData.client && allData.client.length) sheets.push({ name: 'ClientType', data: allData.client });
  if (allData.shareholder && allData.shareholder.length) sheets.push({ name: 'Shareholders', data: allData.shareholder });

  if (sheets.length === 0) { alert('داده‌ای برای خروجی نیست'); return; }

  // Export first sheet as CSV
  const s = sheets[0];
  const f = `filteradium_${s.name}_${new Date().toISOString().split('T')[0]}.csv`;
  const r = await window.api.exportCSV({ data: s.data, filename: f });
  if (r.success) alert(`✅ ذخیره شد:\n${r.path}`);
}

async function exportExcel() {
  const sheets = [];
  if (allData.price && allData.price.length) sheets.push({ name: 'قیمت', data: allData.price });
  if (allData.client && allData.client.length) sheets.push({ name: 'حقیقی_حقوقی', data: allData.client });
  if (allData.shareholder && allData.shareholder.length) sheets.push({ name: 'سهامداران', data: allData.shareholder });

  if (sheets.length === 0) { alert('داده‌ای برای خروجی نیست'); return; }

  const f = `filteradium_${new Date().toISOString().split('T')[0]}.xlsx`;
  const r = await window.api.exportExcelMulti({ sheets, filename: f });
  if (r.success) alert(`✅ ذخیره شد:\n${r.path}`);
}
