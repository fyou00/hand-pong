'use strict';
const pixels = ['00001100100100','00001100100100','00111100100111','00111100100111','00111111111111','00111111111111','11111111111111','01111111111111','00111111111111','00111111111110','00011111111100','00001111111000','00001111111000','00000000000000'];
document.querySelectorAll('.hand').forEach(svg => pixels.forEach((row,y) => [...row].forEach((value,x) => { if(value === '1') { const pixel = document.createElementNS('http://www.w3.org/2000/svg','rect'); pixel.setAttribute('x',x); pixel.setAttribute('y',y); pixel.setAttribute('width','.98'); pixel.setAttribute('height','.98'); svg.append(pixel); } })));
const dialog = document.querySelector('dialog');
let opener;
document.querySelectorAll('[data-start]').forEach(link => link.addEventListener('click', event => { event.preventDefault(); opener = link; dialog.showModal(); }));
document.querySelector('.close').addEventListener('click', () => dialog.close());
dialog.addEventListener('close', () => opener?.focus());
document.querySelector('.copy').addEventListener('click', async () => { const status = document.querySelector('.status'); try { await navigator.clipboard.writeText(document.querySelector('pre code').textContent); status.textContent = 'Perintah berhasil disalin.'; } catch { status.textContent = 'Pilih dan salin teks perintah di atas secara manual.'; } });
