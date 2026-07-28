let allStocks = [];
let selectedStocks = [];
let allData = {};

// ========== TSETMC API (via browser fetch) ==========
const API_URLS = [
  'https://cdn.tsetmc.com',
  'http://cdn.tsetmc.com',
  'https://tsetmc.com',
  'http://tsetmc.com',
];

async function apiFetch(path) {
  for (const base of API_URLS) {
    try {
      const url = base + path;
      console.log('[API] Trying:', url);
      const res = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });
      if (!res.ok) {
        console.log('[API] HTTP', res.status, 'from', base);
        continue;
      }
      const text = await res.text();
      if (!text || !text.trim()) {
        console.log('[API] Empty from', base);
        continue;
      }
      const data = JSON.parse(text);
      console.log('[API] Success from', base);
      return data;
    } catch (e) {
      console.log('[API] Failed:', base, e.message);
    }
  }
  throw new Error('تمام سرورها در دسترس نیستند');
}

// ========== Init ==========
document.addEventListener('DOMContentLoaded', async () => {
  await loadStocks();
  await loadSectors();
  setDefaultDates();
  updateStats();
  window.api.onProgress(updateProgress);
});

async function loadStocks() { allStocks = await window.api.getStocks(); renderSymbolList(allStocks); }

async function loadSectors() {
  const sectors = await window.api.getSectors();
  const sel = document.getElementById('sectorFilter');
  while (sel.options.length > 1) sel.remove(1);
  sectors.forEach(s => { if (s.sector) { const o = document.createElement('option'); o.value = s.sector; o.textContent = s.sector; sel.appendChild(o); } });
}

async function updateStats() {
  const s = await window.api.getStats();
  document.getElementById('statStocks').textContent = s.stocks;
  document.getElementById('statHistory').textContent = s.history;
  document.getElementById('statClients').textContent = s.clientType;
  document.getElementById('statShareholders').textContent = s.shareholders;
}

// ========== Test Connection ==========
async function testConnection() {
  const btn = document.getElementById('btnTest');
  btn.disabled = true;
  btn.innerHTML = '⏳ در حال تست...';
  try {
    const data = await apiFetch('/api/MarketData/GetMarketState');
    alert('✅ اتصال برقرار است!\nسرور TSETMC در دسترس می‌باشد.');
  } catch (e) {
    alert('❌ اتصال برقرار نشد:\n' + e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🔌 تست اتصال';
  }
}

// ========== Fetch from TSETMC ==========
async function fetchAllStocks() {
  const btn = document.getElementById('btnFetchStocks');
  btn.disabled = true;
  btn.innerHTML = '⏳ دریافت...';
  try {
    const data = await apiFetch('/api/ClosingPrice/GetMarketWatch/1/0');
    if (!data || !data.closingPriceAll) throw new Error('داده‌ای دریافت نشد');
    const r = await window.api.saveStocks(data.closingPriceAll);
    alert(`✅ ${r.count} نماد دریافت شد`);
    await loadStocks();
    await loadSectors();
    await updateStats();
  } catch (e) {
    alert('❌ ' + e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🔄 دریافت لیست نمادها از TSETMC';
  }
}

async function fetchData() {
  const btn = document.getElementById('btnFetch');
  btn.disabled = true;
  const types = getSelectedTypes();
  const insCodes = selectedStocks.length > 0 ? selectedStocks : getFilteredStocks().map(s => s.ins_code);

  if (types.length === 0) { alert('لطفاً حداقل یک نوع داده انتخاب کنید'); btn.disabled = false; return; }
  if (insCodes.length === 0) { alert('لطفاً نمادی رو انتخاب کنید'); btn.disabled = false; return; }

  let fetched = { price: 0, client: 0, shareholder: 0 };

  for (let i = 0; i < insCodes.length; i++) {
    const code = insCodes[i];
    btn.innerHTML = `⏳ ${i + 1}/${insCodes.length}`;

    if (types.includes('price')) {
      try {
        const data = await apiFetch(`/api/ClosingPrice/GetClosingPriceHistory/${code}`);
        if (data?.closingPriceHistory) { await window.api.savePriceHistory({ insCode: code, data: data.closingPriceHistory }); fetched.price++; }
      } catch (e) { console.log('Price error:', e.message); }
    }

    if (types.includes('client')) {
      try {
        const data = await apiFetch(`/api/ClientType/GetClientType/${code}/0`);
        if (data) { await window.api.saveClientType({ insCode: code, data }); fetched.client++; }
      } catch (e) { console.log('Client error:', e.message); }
    }

    if (types.includes('shareholder')) {
      try {
        const data = await apiFetch(`/api/Shareholder/GetInstrumentShareholders/${code}`);
        if (data) { await window.api.saveShareholders({ insCode: code, data }); fetched.shareholder++; }
      } catch (e) { console.log('Shareholder error:', e.message); }
    }

    await new Promise(r => setTimeout(r, 200));
  }

  let msg = '✅ دریافت شد:\n';
  if (types.includes('price')) msg += `  📈 قیمت: ${fetched.price} نماد\n`;
  if (types.includes('client')) msg += `  👥 حقیقی/حقوقی: ${fetched.client} نماد\n`;
  if (types.includes('shareholder')) msg += `  🏢 سهامداران: ${fetched.shareholder} نماد`;
  alert(msg);

  btn.disabled = false;
  btn.innerHTML = '🔄 دریافت و ذخیره داده';
  await updateStats();
}

function updateProgress({ current, total }) {
  document.getElementById('btnFetch').innerHTML = `⏳ ${current}/${total}`;
}

function getSelectedTypes() {
  const types = [];
  document.querySelectorAll('.type-check:checked').forEach(cb => types.push(cb.value));
  return types;
}

// ========== Display ==========
async function displayData() {
  const startDate = document.getElementById('startDate').value;
  const endDate = document.getElementById('endDate').value;
  const insCodes = selectedStocks.length > 0 ? selectedStocks : getFilteredStocks().map(s => s.ins_code);
  const types = getSelectedTypes();
  if (!insCodes.length) { alert('نمادی انتخاب نشده'); return; }
  if (!types.length) { alert('نوع داده‌ای انتخاب نشده'); return; }

  const params = { insCodes, startDate, endDate };
  allData = {};
  if (types.includes('price')) allData.price = await window.api.getPriceHistory(params);
  if (types.includes('client')) allData.client = await window.api.getClientType(params);
  if (types.includes('shareholder')) allData.shareholder = await window.api.getShareholders(params);

  if (allData.price?.length) renderTable(allData.price, 'price');
  else if (allData.client?.length) renderTable(allData.client, 'client');
  else if (allData.shareholder?.length) renderTable(allData.shareholder, 'shareholder');
  else { renderTable([], ''); alert('داده‌ای یافت نشد'); }
}

function switchTab(type) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`[data-tab="${type}"]`)?.classList.add('active');
  if (allData[type]) renderTable(allData[type], type);
}

function renderTable(data, type) {
  const head = document.getElementById('tableHead');
  const body = document.getElementById('tableBody');
  const empty = document.getElementById('emptyState');
  const count = document.getElementById('recordCount');

  document.querySelectorAll('.tab-btn').forEach(b => {
    b.style.display = allData[b.dataset.tab]?.length ? '' : 'none';
  });

  if (!data?.length) { head.innerHTML = ''; body.innerHTML = ''; empty.classList.remove('hidden'); count.textContent = '0 رکورد'; return; }

  empty.classList.add('hidden');
  count.textContent = `${data.length.toLocaleString('fa-IR')} رکورد`;
  const keys = Object.keys(data[0]);
  head.innerHTML = `<tr>${keys.map(k => `<th>${T(k)}</th>`).join('')}</tr>`;
  body.innerHTML = data.slice(0, 3000).map(row => '<tr>' + keys.map(k => {
    const v = row[k]; let c = typeof v === 'number' ? 'num' : '';
    if (k.includes('change') || k.includes('pct')) c += v > 0 ? ' positive' : v < 0 ? ' negative' : '';
    return `<td class="${c}">${v != null ? (typeof v === 'number' ? v.toLocaleString('fa-IR') : v) : '-'}</td>`;
  }).join('') + '</tr>').join('');
}

function T(k) {
  const m = { 'id': 'شناسه', 'ins_code': 'کد', 'symbol': 'نماد', 'date': 'تاریخ', 'open': 'اولین', 'high': 'بیشترین', 'low': 'کمترین', 'close': 'پایانی', 'last': 'آخرین', 'volume': 'حجم', 'value': 'ارزش', 'change': 'تغییر', 'change_pct': 'تغییر%', 'name': 'نام', 'sector': 'صنعت', 'individual_buy_count': 'تعداد خرید حقیقی', 'individual_sell_count': 'تعداد فروش حقیقی', 'individual_buy_volume': 'حجم خرید حقیقی', 'individual_sell_volume': 'حجم فروش حقیقی', 'corporate_buy_count': 'تعداد خرید حقوقی', 'corporate_sell_count': 'تعداد فروش حقوقی', 'corporate_buy_volume': 'حجم خرید حقوقی', 'corporate_sell_volume': 'حجم فروش حقوقی', 'data': 'داده', 'updated_at': 'بروزرسانی' };
  return m[k] || k;
}

// ========== UI ==========
function setDefaultDates() {
  const t = new Date(), y = new Date(); y.setFullYear(y.getFullYear() - 1);
  document.getElementById('endDate').value = t.toISOString().split('T')[0];
  document.getElementById('startDate').value = y.toISOString().split('T')[0];
}
function setQuickDate(d) {
  const t = new Date(), p = new Date(); p.setDate(p.getDate() - d);
  document.getElementById('endDate').value = t.toISOString().split('T')[0];
  document.getElementById('startDate').value = p.toISOString().split('T')[0];
}

function renderSymbolList(stocks) {
  const c = document.getElementById('symbolList'); c.innerHTML = '';
  const q = document.getElementById('symbolSearch').value.toLowerCase();
  const sec = document.getElementById('sectorFilter').value;
  let f = stocks;
  if (q) f = f.filter(s => (s.symbol||'').toLowerCase().includes(q) || (s.name||'').toLowerCase().includes(q));
  if (sec !== 'all') f = f.filter(s => s.sector === sec);
  f.forEach(s => {
    const d = document.createElement('div');
    d.className = `symbol-item ${selectedStocks.includes(s.ins_code) ? 'selected' : ''}`;
    d.innerHTML = `<input type="checkbox" ${selectedStocks.includes(s.ins_code) ? 'checked' : ''}><span class="symbol-name">${s.symbol||'?'}</span><span class="symbol-code">${s.sector||''}</span>`;
    d.onclick = () => { const i = selectedStocks.indexOf(s.ins_code); if (i === -1) selectedStocks.push(s.ins_code); else selectedStocks.splice(i, 1); renderSymbolList(allStocks); };
    c.appendChild(d);
  });
}

function getFilteredStocks() { const sec = document.getElementById('sectorFilter').value; return sec === 'all' ? allStocks : allStocks.filter(s => s.sector === sec); }
document.getElementById('symbolSearch').addEventListener('input', () => renderSymbolList(allStocks));
document.getElementById('sectorFilter').addEventListener('change', () => renderSymbolList(allStocks));

// ========== Export ==========
async function exportCSV() {
  const sheets = [];
  if (allData.price?.length) sheets.push({ name: 'Price', data: allData.price });
  if (allData.client?.length) sheets.push({ name: 'ClientType', data: allData.client });
  if (allData.shareholder?.length) sheets.push({ name: 'Shareholders', data: allData.shareholder });
  if (!sheets.length) { alert('داده‌ای برای خروجی نیست'); return; }
  const r = await window.api.exportCSV({ data: sheets[0].data, filename: `filteradium_${sheets[0].name}_${new Date().toISOString().split('T')[0]}.csv` });
  if (r.success) alert(`✅ ذخیره شد:\n${r.path}`);
}

async function exportExcel() {
  const sheets = [];
  if (allData.price?.length) sheets.push({ name: 'قیمت', data: allData.price });
  if (allData.client?.length) sheets.push({ name: 'حقیقی_حقوقی', data: allData.client });
  if (allData.shareholder?.length) sheets.push({ name: 'سهامداران', data: allData.shareholder });
  if (!sheets.length) { alert('داده‌ای برای خروجی نیست'); return; }
  const r = await window.api.exportExcelMulti({ sheets, filename: `filteradium_${new Date().toISOString().split('T')[0]}.xlsx` });
  if (r.success) alert(`✅ ذخیره شد:\n${r.path}`);
}
