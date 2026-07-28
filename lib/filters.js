// ===== فیلترادیوم - Filter Engine =====

// فیلترهای آماده
const PRE_FILTERS = {
  momentum: {
    name: "مومنتوم قوی",
    conditions: [
      { field: "plp", operator: ">", value: 2 },
      { field: "tvol", operator: ">", value: 1000000 },
      { field: "pcp", operator: ">", value: 0 }
    ]
  },
  value: {
    name: "سهم‌های ارزان",
    conditions: [
      { field: "pe", operator: ">", value: 0 },
      { field: "pe", operator: "<", value: 10 },
      { field: "eps", operator: ">", value: 500 },
      { field: "tvol", operator: ">", value: 500000 }
    ]
  },
  smart_money: {
    name: "ورود پول هوشمند",
    conditions: [
      { field: "buy_ratio", operator: ">", value: 1.5 },
      { field: "tvol", operator: ">", value: 1000000 },
      { field: "pcp", operator: ">", value: 0 }
    ]
  },
  oversold: {
    name: "اُورسولد",
    conditions: [
      { field: "plp", operator: "<", value: -3 },
      { field: "tvol", operator: ">", value: 500000 },
      { field: "pe", operator: ">", value: 0 }
    ]
  },
  breakout: {
    name: "شکست مقاومت",
    conditions: [
      { field: "pl", operator: ">", value: 0 },
      { field: "tvol", operator: ">", value: 2000000 },
      { field: "plp", operator: ">", value: 1 }
    ]
  },
  dividend: {
    name: "سهامداری",
    conditions: [
      { field: "pe", operator: ">", value: 0 },
      { field: "pe", operator: "<", value: 8 },
      { field: "eps", operator: ">", value: 1000 },
      { field: "tvol", operator: ">", value: 1000000 }
    ]
  }
};

// فیلدهای قابل استفاده
const FIELDS = {
  plp: { name: "درصد تغییر قیمت", unit: "%" },
  pcp: { name: "درصد تغییر پایانی", unit: "%" },
  tvol: { name: "حجم معاملات", unit: "سهم" },
  tval: { name: "ارزش معاملات", unit: "ریال" },
  pe: { name: "نسبت قیمت به سود", unit: "" },
  eps: { name: "سود هر سهم", unit: "ریال" },
  pl: { name: "آخرین قیمت", unit: "ریال" },
  buy_ratio: { name: "نسبت خرید به فروش", unit: "" }
};

// نمایش شرایط فیلتر
function renderConditions() {
  const container = document.getElementById('filter-conditions');
  const conditions = container.querySelectorAll('.condition-row');
  
  let code = '// فیلتر فیلترادیوم\n';
  code += '// ─────────────────\n\n';
  
  conditions.forEach((row, index) => {
    const field = row.querySelector('.condition-field').value;
    const operator = row.querySelector('.condition-operator').value;
    const value = row.querySelector('.condition-value').value;
    
    if (field && value) {
      const fieldName = FIELDS[field] ? FIELDS[field].name : field;
      code += `(${field}) ${operator} ${value}  // ${fieldName}\n`;
      
      if (index < conditions.length - 1) {
        code += 'AND\n';
      }
    }
  });
  
  document.getElementById('filter-code').textContent = code;
}

// افزودن شرط
function addCondition() {
  const container = document.getElementById('filter-conditions');
  const newRow = document.createElement('div');
  newRow.className = 'condition-row';
  newRow.innerHTML = `
    <select class="condition-field" onchange="renderConditions()">
      <option value="">انتخاب کنید...</option>
      <option value="plp">درصد تغییر قیمت</option>
      <option value="tvol">حجم معاملات</option>
      <option value="tval">ارزش معاملات</option>
      <option value="pe">نسبت قیمت به سود</option>
      <option value="eps">سود هر سهم</option>
      <option value="buy_ratio">نسبت خرید به فروش</option>
      <option value="pl">آخرین قیمت</option>
      <option value="pcp">درصد تغییر پایانی</option>
    </select>
    <select class="condition-operator" onchange="renderConditions()">
      <option value=">">بزرگتر از</option>
      <option value="<">کوچکتر از</option>
      <option value=">=">بزرگتر مساوی</option>
      <option value="<=">کوچکتر مساوی</option>
      <option value="==">مساوی</option>
    </select>
    <input type="number" class="condition-value" placeholder="مقدار" oninput="renderConditions()">
    <button class="btn-remove" onclick="removeCondition(this)">✕</button>
  `;
  container.appendChild(newRow);
  renderConditions();
}

// حذف شرط
function removeCondition(btn) {
  const container = document.getElementById('filter-conditions');
  if (container.children.length > 1) {
    btn.parentElement.remove();
    renderConditions();
  }
}

// بارگذاری فیلتر آماده
function loadPreFilter(filterName) {
  const filter = PRE_FILTERS[filterName];
  if (!filter) return;
  
  const container = document.getElementById('filter-conditions');
  container.innerHTML = '';
  
  filter.conditions.forEach(cond => {
    const row = document.createElement('div');
    row.className = 'condition-row';
    row.innerHTML = `
      <select class="condition-field" onchange="renderConditions()">
        <option value="">انتخاب کنید...</option>
        <option value="plp" ${cond.field === 'plp' ? 'selected' : ''}>درصد تغییر قیمت</option>
        <option value="tvol" ${cond.field === 'tvol' ? 'selected' : ''}>حجم معاملات</option>
        <option value="tval" ${cond.field === 'tval' ? 'selected' : ''}>ارزش معاملات</option>
        <option value="pe" ${cond.field === 'pe' ? 'selected' : ''}>نسبت قیمت به سود</option>
        <option value="eps" ${cond.field === 'eps' ? 'selected' : ''}>سود هر سهم</option>
        <option value="buy_ratio" ${cond.field === 'buy_ratio' ? 'selected' : ''}>نسبت خرید به فروش</option>
        <option value="pl" ${cond.field === 'pl' ? 'selected' : ''}>آخرین قیمت</option>
        <option value="pcp" ${cond.field === 'pcp' ? 'selected' : ''}>درصد تغییر پایانی</option>
      </select>
      <select class="condition-operator" onchange="renderConditions()">
        <option value=">" ${cond.operator === '>' ? 'selected' : ''}>بزرگتر از</option>
        <option value="<" ${cond.operator === '<' ? 'selected' : ''}>کوچکتر از</option>
        <option value=">=" ${cond.operator === '>=' ? 'selected' : ''}>بزرگتر مساوی</option>
        <option value="<=" ${cond.operator === '<=' ? 'selected' : ''}>کوچکتر مساوی</option>
        <option value="==" ${cond.operator === '==' ? 'selected' : ''}>مساوی</option>
      </select>
      <input type="number" class="condition-value" placeholder="مقدار" value="${cond.value}" oninput="renderConditions()">
      <button class="btn-remove" onclick="removeCondition(this)">✕</button>
    `;
    container.appendChild(row);
  });
  
  renderConditions();
}

// اجرای فیلتر ( شبیه‌سازی )
function runFilter() {
  const startTime = Date.now();
  
  // داده‌های نمونه (بعداً از API واقعی)
  const sampleData = generateSampleData();
  
  // دریافت شرایط فیلتر
  const conditions = getFilterConditions();
  
  // اعمال فیلتر
  const results = sampleData.filter(stock => {
    return conditions.every(cond => {
      const value = stock[cond.field];
      switch(cond.operator) {
        case '>': return value > cond.value;
        case '<': return value < cond.value;
        case '>=': return value >= cond.value;
        case '<=': return value <= cond.value;
        case '==': return value == cond.value;
        default: return true;
      }
    });
  });
  
  const elapsed = Date.now() - startTime;
  
  // نمایش نتایج
  displayResults(results, elapsed);
}

// دریافت شرایط فیلتر
function getFilterConditions() {
  const conditions = [];
  const rows = document.querySelectorAll('#filter-conditions .condition-row');
  
  rows.forEach(row => {
    const field = row.querySelector('.condition-field').value;
    const operator = row.querySelector('.condition-operator').value;
    const value = parseFloat(row.querySelector('.condition-value').value);
    
    if (field && !isNaN(value)) {
      conditions.push({ field, operator, value });
    }
  });
  
  return conditions;
}

// نمایش نتایج
function displayResults(results, elapsed) {
  const panel = document.getElementById('results');
  const tbody = document.getElementById('results-body');
  const countEl = document.getElementById('result-count');
  const timeEl = document.getElementById('result-time');
  
  panel.style.display = 'block';
  countEl.textContent = `${results.length} نتیجه`;
  timeEl.textContent = `زمان اجرا: ${elapsed}ms`;
  
  tbody.innerHTML = results.map(stock => `
    <tr>
      <td><strong>${stock.symbol}</strong></td>
      <td>${stock.name}</td>
      <td>${formatNumber(stock.pl)}</td>
      <td class="${stock.plp >= 0 ? 'text-green' : 'text-red'}">${stock.plp >= 0 ? '+' : ''}${stock.plp.toFixed(2)}%</td>
      <td>${formatNumber(stock.tvol)}</td>
      <td><strong>${stock.score}</strong></td>
      <td><button class="btn btn-primary" style="padding: 6px 12px; font-size: 12px;">مشاهده</button></td>
    </tr>
  `).join('');
  
  // اسکرول به نتایج
  panel.scrollIntoView({ behavior: 'smooth' });
}

// فرمت عدد
function formatNumber(num) {
  if (num >= 1000000000) return (num / 1000000000).toFixed(1) + 'M';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

// تولید داده نمونه
function generateSampleData() {
  const symbols = [
    { symbol: "خساپا", name: "ایران خودرو" },
    { symbol: "فولاد", name: "فولاد مبارکه" },
    { symbol: "شپنا", name: "پالایش نفت اصفهان" },
    { symbol: "شبندر", name: "پالایش نفت بندر عباس" },
    { symbol: "خودرو", name: "ایران خودرو" },
    { symbol: "فملی", name: "ملی مس ایران" },
    { symbol: "کگل", name: "گل گهر" },
    { symbol: "جم", name: "پتروشیمی جم" },
    { symbol: "وبملت", name: "بانک ملت" },
    { symbol: "تاپیکو", name: "نفت و گاز تأمین" },
    { symbol: "سمات", name: "سامان‌گستر" },
    { symbol: "کمند", name: "صندوق کمند" },
    { symbol: "آگاس", name: "صندوق آگاس" },
    { symbol: "های وب", name: "های وب" },
    { symbol: "دی", name: "بانک دی" },
    { symbol: "خپارس", name: "پارس خودرو" },
    { symbol: "سایپا", name: "سایپا" },
    { symbol: "پترول", name: "پتروشیمی امیرکبیر" },
    { symbol: "شتران", name: "پالایش نفت تهران" },
    { symbol: "خاهن", name: "آهنگری اهواز" }
  ];
  
  return symbols.map(s => ({
    ...s,
    pl: Math.floor(Math.random() * 50000) + 1000,
    plp: (Math.random() * 10 - 5).toFixed(2),
    pcp: (Math.random() * 8 - 4).toFixed(2),
    tvol: Math.floor(Math.random() * 50000000) + 100000,
    tval: Math.floor(Math.random() * 500000000000) + 1000000000,
    pe: Math.floor(Math.random() * 30) + 1,
    eps: Math.floor(Math.random() * 2000) - 500,
    buy_ratio: (Math.random() * 3 + 0.5).toFixed(2),
    score: Math.floor(Math.random() * 40) + 60
  }));
}
