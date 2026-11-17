"use strict";
const copy = document.querySelector('.copy');
copy.addEventListener('click', async () => {
  const status = document.querySelector('.status');
  copy.disabled = true;
  copy.setAttribute('aria-busy', 'true');
  status.textContent = 'Menyalin perintah…';
  try {
    await navigator.clipboard.writeText(document.querySelector('pre code').textContent);
    status.textContent = 'Perintah berhasil disalin.';
  } catch {
    status.textContent = 'Tidak dapat menyalin otomatis. Pilih dan salin perintah di atas.';
  } finally {
    copy.disabled = false;
    copy.removeAttribute('aria-busy');
  }
});

const themeToggle = document.querySelector('.theme-toggle');
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  themeToggle.setAttribute('aria-pressed', String(theme === 'dark'));
  themeToggle.setAttribute('aria-label', theme === 'dark' ? 'Aktifkan mode terang' : 'Aktifkan mode gelap');
  themeToggle.title = themeToggle.getAttribute('aria-label');
  document.querySelector('meta[name="theme-color"]').content = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
}
applyTheme(document.documentElement.dataset.theme === 'light' ? 'light' : 'dark');
themeToggle.hidden = false;
themeToggle.addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  try { localStorage.setItem('palm-pong-theme', next); } catch {}
});
