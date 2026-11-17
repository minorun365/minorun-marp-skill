// SVG の図が詰まっていないかを、実際にレンダリングして測る。
// 使い方: node tools/check-svg-spacing.mjs <svg...>   （下限は viewBox 座標系）
//
// 箱の中の文字の余白は check-svg-box-fit.mjs が見る。こちらは図の要素どうしの間隔を見る。
//   ① 並んだ箱どうしの隙間（28px以上。6px以下でくっつけた箱は、ひと続きの帯として通す）
//   ② 文字の行どうしの隙間（文字の高さの45%以上）
//   ③ 塗った面の上に、別の色で塗った箱を重ねていないか（境目が見えにくい）
//   ④ 矢印・線と、そのラベルの文字の間（20px以上）
//   ⑤ 挿絵（image）と線・文字の間（14px以上）
//   ⑥ 囲み枠と中の箱の間（14px以上）、同じ行に横並びの文字どうしの間（28px以上）
// 仕組み: ヘッドレス Chrome で SVG を開き、rect・text・image の実寸を getBBox() で取って比べる。
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
const BOX_GAP = 28;        // ① 並んだ箱の隙間の下限
const FRAME_PAD = 14;      // ⑥ 囲み枠と中の箱の間の下限
const SEG = 6;             //    これ以下でくっつけた箱は、層や帯グラフのようなひと続きの積み木として通す
const LINE_GAP = 0.45;     // ② 行の隙間の下限（文字の高さに対する比）
const LINE_PAD = 20;       // ④ 矢印・線と文字の間の下限
const IMG_PAD = 14;        // ⑤ 挿絵と線・文字の間の下限
const files = process.argv.slice(2);
if (!files.length) { console.error('svg を指定'); process.exit(2); }
const browser = await puppeteer.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage();
let ng = 0;
for (const f of files) {
  const svg = fs.readFileSync(f, 'utf8');
  await page.setContent(`<html><body style="margin:0;background:#fff">${svg}</body></html>`);
  await page.evaluate(() => document.fonts.ready);
  const res = await page.evaluate((BOX_GAP, LINE_GAP, SEG, LINE_PAD, IMG_PAD, FRAME_PAD) => {
    const svg = document.querySelector('svg');
    const vb = svg.viewBox.baseVal;
    const out = [];
    const filled = r => { const c = (r.getAttribute('fill') || '').toLowerCase(); return c && c !== 'none' && c !== '#ffffff' && c !== '#fff' && c !== 'white'; };
    const rects = [...svg.querySelectorAll('rect')]
      .map(r => ({ x: +r.getAttribute('x'), y: +r.getAttribute('y'), w: +r.getAttribute('width'), h: +r.getAttribute('height'), fill: filled(r) }))
      .filter(r => r.w >= 60 && r.h >= 40)                               // 棒グラフの棒・線は対象外
      .filter(r => !(r.x === vb.x && r.y === vb.y && r.w === vb.width && r.h === vb.height));
    const inside = (a, b) => a.x >= b.x && a.y >= b.y && a.x + a.w <= b.x + b.w && a.y + a.h <= b.y + b.h;
    const ov = (a0, a1, b0, b1) => Math.min(a1, b1) - Math.max(a0, b0);
    for (const a of rects) for (const b of rects) {
      if (a === b) continue;
      if (inside(a, b)) { if (a.fill && b.fill) out.push(`塗った面の上に塗った箱を重ねている（境目が見えにくい） 箱 ${a.x},${a.y} ${a.w}x${a.h}`); continue; }
      if (inside(b, a)) continue;
      // 横に並ぶ箱：縦が半分以上重なり、b が a の右にある
      const vo = ov(a.y, a.y + a.h, b.y, b.y + b.h), ho = ov(a.x, a.x + a.w, b.x, b.x + b.w);
      const gx = b.x - (a.x + a.w), gy = b.y - (a.y + a.h);
      if (vo > Math.min(a.h, b.h) * 0.5 && gx > SEG && gx < BOX_GAP) out.push(`横に並ぶ箱の隙間が ${Math.round(gx)}px（${BOX_GAP}px以上） 箱 ${a.x},${a.y} と ${b.x},${b.y}`);
      if (ho > Math.min(a.w, b.w) * 0.5 && gy > SEG && gy < BOX_GAP) out.push(`縦に並ぶ箱の隙間が ${Math.round(gy)}px（${BOX_GAP}px以上） 箱 ${a.x},${a.y} と ${b.x},${b.y}`);
    }
    // ⑥ 囲み枠（白地に線の箱・閉じたパスの吹き出し）と、中の箱の間が狭い（枠に中身が張り付く）
    const frames = [
      ...[...svg.querySelectorAll('rect')].filter(r => !filled(r) && (r.getAttribute('stroke') || 'none') !== 'none' && !r.getAttribute('stroke-dasharray'))
        .map(r => ({ x: +r.getAttribute('x'), y: +r.getAttribute('y'), w: +r.getAttribute('width'), h: +r.getAttribute('height') })),
      ...[...svg.querySelectorAll('path')].filter(q => /z\s*$/i.test(q.getAttribute('d') || '') && !filled(q) && (q.getAttribute('stroke') || 'none') !== 'none')
        .map(q => { const b = q.getBBox(); return { x: b.x, y: b.y, w: b.width, h: b.height }; }),
    ].filter(r => r.w >= 120 && r.h >= 60);
    for (const fr of frames) for (const r of rects) {
      if (r.x === fr.x && r.y === fr.y && r.w === fr.w && r.h === fr.h) continue;
      if (!(r.x >= fr.x - 2 && r.y >= fr.y - 2 && r.x + r.w <= fr.x + fr.w + 2 && r.y + r.h <= fr.y + fr.h + 2)) continue;
      const pad = Math.min(r.y - fr.y, fr.y + fr.h - (r.y + r.h));   // 上下。左右は端の箱だけが枠に近いので縦で測る
      if (pad < FRAME_PAD) out.push(`囲み枠と中の箱の間が ${Math.round(pad)}px（${FRAME_PAD}px以上） 箱 ${r.x},${r.y}`);
    }
    const texts = [...svg.querySelectorAll('text')].map(t => { const b = t.getBBox(); return { s: t.textContent.trim(), x: b.x, y: b.y, w: b.width, h: b.height }; });
    for (const a of texts) for (const b of texts) {
      if (a === b || !a.s || !b.s) continue;
      const ho = ov(a.x, a.x + a.w, b.x, b.x + b.w), gy = b.y - (a.y + a.h);
      if (ho > 0 && gy >= -2 && gy < Math.min(a.h, b.h) * LINE_GAP) {
        // 間に別の文字が挟まっていない、すぐ下の行だけを見る
        const between = texts.some(c => c !== a && c !== b && c.y >= a.y + a.h - 2 && c.y + c.h <= b.y + 2 && ov(a.x, a.x + a.w, c.x, c.x + c.w) > 0);
        if (!between) out.push(`行が詰まっている「${a.s.slice(0, 14)}」と「${b.s.slice(0, 14)}」の間 ${Math.round(gy)}px（文字の高さの${Math.round(LINE_GAP * 100)}%以上）`);
      }
    }
    // ④ 矢印・線と文字が近すぎる（矢印の上下のラベルが線に張り付く）。打ち消し線と✕印は対象外
    const segs = [...svg.querySelectorAll('line')].map(l => ({ x1: +l.getAttribute('x1'), y1: +l.getAttribute('y1'), x2: +l.getAttribute('x2'), y2: +l.getAttribute('y2') }))
      .filter(l => Math.hypot(l.x2 - l.x1, l.y2 - l.y1) >= 40);
    for (const t of texts) for (const l of segs) {
      if (!t.s) continue;
      const lx0 = Math.min(l.x1, l.x2), lx1 = Math.max(l.x1, l.x2), ly0 = Math.min(l.y1, l.y2), ly1 = Math.max(l.y1, l.y2);
      const dx = Math.max(0, lx0 - (t.x + t.w), t.x - lx1), dy = Math.max(0, ly0 - (t.y + t.h), t.y - ly1);
      if (dx === 0 && dy === 0) continue;                       // 文字を横切る線（打ち消し線）は意図したもの
      const d = Math.hypot(dx, dy);
      if (d < LINE_PAD) out.push(`矢印・線と文字「${t.s.slice(0, 14)}」の間が ${Math.round(d)}px（${LINE_PAD}px以上）`);
    }
    // ⑥ 同じ行に横並びの文字どうしが近すぎる（項目名と数値が張り付く）。28px以上あける
    for (const a of texts) for (const b of texts) {
      if (a === b || !a.s || !b.s) continue;
      if (a.s.length <= 2) continue;   // 丸の中の番号・記号は、右の名前と組で1つのまとまり
      const vo = ov(a.y, a.y + a.h, b.y, b.y + b.h), gx = b.x - (a.x + a.w);
      if (vo > Math.min(a.h, b.h) * 0.5 && gx > -a.w * 0.5 && gx < BOX_GAP) out.push(`横に並ぶ文字「${a.s.slice(0, 14)}」と「${b.s.slice(0, 14)}」の間が ${Math.round(gx)}px（${BOX_GAP}px以上）`);
    }
    // ⑤ 挿絵（image）と線・文字が近すぎる。挿絵の縁から線や文字まで14px以上あける。
    const imgs = [...svg.querySelectorAll('image')].map(i => { const b = i.getBBox(); return { x: b.x, y: b.y, w: b.width, h: b.height }; })
      .filter(i => i.w >= 40 && i.h >= 40);
    const gap = (a, b) => Math.hypot(Math.max(0, b.x - (a.x + a.w), a.x - (b.x + b.w)), Math.max(0, b.y - (a.y + a.h), a.y - (b.y + b.h)));
    for (const im of imgs) {
      // 斜めの矢印は四角で近似せず、線分と挿絵の四角の実距離で測る
      const pt = (px, py) => Math.hypot(Math.max(0, im.x - px, px - (im.x + im.w)), Math.max(0, im.y - py, py - (im.y + im.h)));
      for (const l of segs) {
        let d = Infinity;
        for (let k = 0; k <= 200; k++) d = Math.min(d, pt(l.x1 + (l.x2 - l.x1) * k / 200, l.y1 + (l.y2 - l.y1) * k / 200));
        if (d > 0 && d < IMG_PAD) out.push(`挿絵 ${Math.round(im.x)},${Math.round(im.y)} と線の間が ${Math.round(d)}px（${IMG_PAD}px以上）`);
      }
      for (const t of texts) {
        if (!t.s) continue;
        const d = gap(im, t);
        // 縁にかかった文字（一部だけ挿絵に重なる）も拾う。重なると距離が0になり、d > 0 の判定だけでは素通りする。
        // 挿絵の中に丸ごと収まる文字は、絵の上に載せたラベルとして外す
        const inside = t.x >= im.x && t.y >= im.y && t.x + t.w <= im.x + im.w && t.y + t.h <= im.y + im.h;
        if (d === 0 && !inside) out.push(`挿絵 ${Math.round(im.x)},${Math.round(im.y)} と文字「${t.s.slice(0, 14)}」が重なっている（${IMG_PAD}px以上あける）`);
        if (d > 0 && d < IMG_PAD) out.push(`挿絵 ${Math.round(im.x)},${Math.round(im.y)} と文字「${t.s.slice(0, 14)}」の間が ${Math.round(d)}px（${IMG_PAD}px以上）`);
      }
    }
    return [...new Set(out)];
  }, BOX_GAP, LINE_GAP, SEG, LINE_PAD, IMG_PAD, FRAME_PAD);
  for (const r of res) { ng++; console.log(`NG ${path.basename(f)} ${r}`); }
}
await browser.close();
console.log(`${files.length} ファイルを走査、NG ${ng} 件`);
process.exit(ng ? 1 : 0);
