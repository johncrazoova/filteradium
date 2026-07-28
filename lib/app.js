// ===== فیلترادیوم - App =====

document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 فیلترادیوم لود شد');
  
  // رندر اولیه شرایط
  renderConditions();
  
  // رویداد تغییر فیلترها
  document.getElementById('filter-conditions').addEventListener('input', renderConditions);
  document.getElementById('filter-conditions').addEventListener('change', renderConditions);
  
  // انیمیشن اسکرول
  initScrollAnimation();
});

// انیمیشن اسکرول
function initScrollAnimation() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });
  
  document.querySelectorAll('.feature-card, .prefilter-card, .pricing-card').forEach(el => {
    observer.observe(el);
  });
}

// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});
