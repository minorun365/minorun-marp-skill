// SVG の <text> が、重なっている <rect> の内側に余白つきで収まっているかを、実際にレンダリングして測る。
// 使い方: node tools/check-svg-box-fit.mjs <svg...>   （余白の下限は 14px。viewBox 座標系）
// 仕組み: ヘッドレス Chrome で SVG を開き、getBBox() で文字の実寸を取り、中心を含む rect と比べる。
//        フォントの字幅はソースからは分からないので、描画して測る以外に確かめる方法が無い。
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
// puppeteer-core は marp-cli に同梱されているものを借りる。場所が違うときは MARP_NODE_MODULES で指定する
const globalRoot = process.env.MARP_NODE_MODULES
  || path.join(execSync('npm root -g').toString().trim(), '@marp-team/marp-cli/node_modules/');
const require = createRequire(globalRoot.endsWith('/') ? globalRoot : globalRoot + '/');
const puppeteer = require('puppeteer-core');
// Chrome の場所は CHROME_PATH で上書きできる
const CHROME = process.env.CHROME_PATH || (process.platform === 'darwin'
  ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  : process.platform === 'win32'
    ? 'C:/Program Files/Google/Chrome/Application/chrome.exe'
    : '/usr/bin/google-chrome');
const MIN = 14;
const files = process.argv.slice(2);
if (!files.length) { console.error('svg を指定'); process.exit(2); }
const browser = await puppeteer.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage();
let ng = 0, scanned = 0;
for (const f of files) {
  const svg = fs.readFileSync(f, 'utf8');
  await page.setContent(`<html><body style="margin:0;background:#000">${svg}</body></html>`);
  await page.evaluate(() => document.fonts.ready);
  const res = await page.evaluate(() => {
    const svg = document.querySelector('svg');
    const vb = svg.viewBox.baseVal;
    const rects = [...svg.querySelectorAll('rect')].filter(r => !(r.getAttribute('x') === null))
      .map(r => ({ x: +r.getAttribute('x'), y: +r.getAttribute('y'), w: +r.getAttribute('width'), h: +r.getAttribute('height') }))
      .filter(r => !(r.x === 0 && r.y === 0 && r.w === vb.width && r.h === vb.height)); // 背景は除く
    const out = [];
    for (const t of svg.querySelectorAll('text')) {
      const b = t.getBBox();
      const cx = b.x + b.width / 2, cy = b.y + b.height / 2;
      const box = rects.find(r => cx >= r.x && cx <= r.x + r.w && cy >= r.y && cy <= r.y + r.h);
      out.push({ text: t.textContent.trim(), bbox: [b.x, b.y, b.width, b.height].map(v => Math.round(v)),
        box: box ? [box.x, box.y, box.w, box.h] : null,
        margins: box ? { left: Math.round(b.x - box.x), right: Math.round(box.x + box.w - (b.x + b.width)), top: Math.round(b.y - box.y), bottom: Math.round(box.y + box.h - (b.y + b.height)) } : null,
        overflowVB: b.x < 0 || b.y < 0 || b.x + b.width > vb.width || b.y + b.height > vb.height });
    }
    return out;
  });
  for (const r of res) {
    scanned++;
    const bad = [];
    if (r.margins) for (const [k, v] of Object.entries(r.margins)) if (v < MIN) bad.push(`${k} ${v}px`);
    if (r.overflowVB) bad.push('viewBox の外');
    if (bad.length) { ng++; console.log(`NG ${path.basename(f)} 「${r.text}」 ${bad.join(' / ')}  bbox=${r.bbox}`); }
  }
}
await browser.close();
console.log(`${files.length} ファイル・文字 ${scanned} 件を走査、NG ${ng} 件`);
process.exit(ng ? 1 : 0);
