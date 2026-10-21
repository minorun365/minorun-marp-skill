// 図形（吹き出し・しっぽ・箱・線・矢印）が、真下の面と同じ色で沈んでいないかを明度比で測る。
// 使い方: node tools/check-svg-contrast.mjs <svg...> [--bg #000000] [--png <出力フォルダ>]
// 黒地の図で、吹き出しを箱と同じ暗いグラデーションで塗ると消える。この崩れは文字の検査
// （check-svg-box-fit）にも余白の検査にも引っかからないので、専用に測る。
// 真下の面は「その図形より前に描かれ、図形の中心を含む最小の rect」。無ければ背景色。
// 明度比 1.25 未満で NG。--png を付けると、目視用に背景色の上へ描いた PNG も書き出す。
// 図全体の 20% を超える大きな面（ゾーン・広がりの帯）は、意図して淡く敷く面なので対象外。
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

const args = process.argv.slice(2);
const bgIdx = args.indexOf('--bg'); const BG = bgIdx >= 0 ? args.splice(bgIdx, 2)[1] : '#000000';
const pngIdx = args.indexOf('--png'); const PNG = pngIdx >= 0 ? args.splice(pngIdx, 2)[1] : null;
const MIN = 1.25;
const files = args;
if (!files.length) { console.error('使い方: node tools/check-svg-contrast.mjs <svg...> [--bg #000000] [--png <dir>]'); process.exit(2); }

const browser = await puppeteer.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 900, deviceScaleFactor: 1.5 });
let ng = 0, scanned = 0;
for (const f of files) {
  const svg = fs.readFileSync(f, 'utf8');
  await page.setContent(`<html><body style="margin:0;background:${BG}"><div id="w" style="width:1200px">${svg}</div></body></html>`);
  await page.evaluate(() => { const s = document.querySelector('svg'); s.style.width = '1200px'; s.style.height = 'auto'; });
  const res = await page.evaluate((BG) => {
    const svg = document.querySelector('svg');
    const hex = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const [r, g, b, a = 1] = m[1].split(',').map(Number); return a === 0 ? null : [r, g, b]; };
    const parseHex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
    const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
    // グラデーションは stop の平均色で代表させる
    const paint = (el, prop) => {
      const v = getComputedStyle(el)[prop];
      if (!v || v === 'none') return null;
      const u = v.match(/url\("?#([^")]+)"?\)/);
      if (u) {
        const g = document.getElementById(u[1]); if (!g) return null;
        const cs = [...g.querySelectorAll('stop')].map(s => hex(getComputedStyle(s).stopColor)).filter(Boolean);
        if (!cs.length) return null;
        return [0, 1, 2].map(i => cs.reduce((a, c) => a + c[i], 0) / cs.length);
      }
      return hex(v);
    };
    const shapes = [...svg.querySelectorAll('rect,polygon,path,ellipse,circle,line,polyline')].filter(e => !e.closest('defs,marker'));
    const rects = shapes.filter(e => e.tagName === 'rect').map(e => ({ e, b: e.getBBox(), c: paint(e, 'fill') })).filter(r => r.c);
    const order = new Map(shapes.map((e, i) => [e, i]));
    const out = [];
    for (const e of shapes) {
      const isLine = ['line', 'polyline'].includes(e.tagName) || paint(e, 'fill') === null;
      const col = isLine ? paint(e, 'stroke') : paint(e, 'fill');
      if (!col) continue;
      const b = e.getBBox(); const cx = b.x + b.width / 2, cy = b.y + b.height / 2;
      const vb = svg.viewBox.baseVal;
      if (b.width * b.height > 0.2 * vb.width * vb.height) continue;
      const under = rects.filter(r => r.e !== e && order.get(r.e) < order.get(e) &&
        cx >= r.b.x && cx <= r.b.x + r.b.width && cy >= r.b.y && cy <= r.b.y + r.b.height)
        .sort((p, q) => p.b.width * p.b.height - q.b.width * q.b.height)[0];
      const base = under ? under.c : parseHex(BG);
      out.push({ tag: e.tagName, at: [b.x, b.y, b.width, b.height].map(Math.round), r: +ratio(col, base).toFixed(2), on: under ? 'rect' : '背景' });
    }
    return out;
  }, BG);
  for (const r of res) {
    scanned++;
    if (r.r < MIN) { ng++; console.log(`NG ${path.basename(f)} <${r.tag}> at ${r.at} 明度比 ${r.r}（下の${r.on}とほぼ同じ色）`); }
  }
  if (PNG) { fs.mkdirSync(PNG, { recursive: true }); await (await page.$('#w')).screenshot({ path: path.join(PNG, path.basename(f, '.svg') + '.png') }); }
}
await browser.close();
console.log(`${files.length} ファイル・図形 ${scanned} 個を走査、NG ${ng} 件`);
process.exit(ng ? 1 : 0);
