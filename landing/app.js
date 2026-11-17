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
