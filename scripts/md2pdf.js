// md -> html (KaTeX pre-rendered) -> PDF via headless Chromium (Edge/Chrome).
// Offline: no Word, no LibreOffice, no LaTeX.
//
// usage: node md2pdf.js <input.md> <output.pdf> [title] [subtitle]
//        node md2pdf.js --selftest
// env:   MD2PDF_EDGE        explicit browser executable
//        MD2PDF_LINE_ORIENTED=0  keep normal markdown paragraph merging (default: one paragraph per source line, Chinese only)
//        MD2PDF_LANG=en|zh       force the layout language (default: auto-detect from the source text)
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const MarkdownIt = require('markdown-it');
const katex = require('katex');

// Browsers we can drive. Windows paths first (the original platform), then the
// macOS app-bundle paths, then the usual Linux binary locations; finally we scan
// PATH so Nix/Homebrew/flatpak installs are found too.
const BROWSER_CANDIDATES = [
  process.env.MD2PDF_EDGE,
  // Windows
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  // macOS
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  // Linux
  '/usr/bin/google-chrome',
  '/usr/bin/google-chrome-stable',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
  '/snap/bin/chromium',
  '/usr/bin/microsoft-edge',
  '/usr/bin/microsoft-edge-stable',
].filter(Boolean);

const BROWSER_NAMES = [
  'msedge', 'chrome', 'google-chrome', 'google-chrome-stable',
  'chromium', 'chromium-browser', 'microsoft-edge', 'microsoft-edge-stable',
];

const findInPath = (name) => {
  const exts = process.platform === 'win32' ? ['', '.exe'] : [''];
  for (const dir of (process.env.PATH || '').split(path.delimiter).filter(Boolean)) {
    for (const ext of exts) {
      const candidate = path.join(dir, name + ext);
      try {
        if (fs.statSync(candidate).isFile()) return candidate;
      } catch { /* not here */ }
    }
  }
  return null;
};

const findBrowser = () => {
  const direct = BROWSER_CANDIDATES.find((p) => fs.existsSync(p));
  if (direct) return direct;
  for (const name of BROWSER_NAMES) {
    const hit = findInPath(name);
    if (hit) return hit;
  }
  return null;
};

const banner = (msg) => console.log(msg);

// ---- doctor: one command a buyer can run when something looks wrong ----
const runQuiet = (cmd, args) => {
  try {
    const out = execFileSync(cmd, args, { stdio: ['ignore', 'pipe', 'ignore'], timeout: 15000 });
    return { ok: true, out: String(out).trim() };
  } catch {
    return { ok: false, out: '' };
  }
};

if (process.argv[2] === '--doctor' || process.argv[2] === '--selftest') {
  const browser = findBrowser();
  const nodeMajor = Number(process.versions.node.split('.')[0]);
  const katexFonts = path.join(__dirname, 'node_modules', 'katex', 'dist', 'fonts');
  const hasKatexFonts = fs.existsSync(katexFonts);

  const pyCmd = ['python3', 'python'].find((c) => runQuiet(c, ['-c', 'import pymupdf']).ok);
  const pyVer = pyCmd ? runQuiet(pyCmd, ['-c', 'import pymupdf;print(pymupdf.__version__)']).out : '';
  const typstBin = findInPath('typst') || ['/usr/local/bin/typst', '/opt/homebrew/bin/typst'].find((p) => fs.existsSync(p));
  const fc = runQuiet('fc-list', [':lang=zh']);
  const cjkFaces = fc.ok ? fc.out.split('\n').filter(Boolean).length : null;

  // [name, state, detail, blocking]
  const rows = [
    ['node', nodeMajor >= 18 ? 'ok' : 'too old', `${process.version} (need >= 18)`, nodeMajor >= 18],
    ['katex fonts', hasKatexFonts ? 'ok' : 'missing', hasKatexFonts ? 'vendored' : 're-clone the repo, the fonts ship with it', hasKatexFonts],
    ['browser', browser ? 'ok' : 'not found', browser || 'set MD2PDF_EDGE, install Chrome, or use the Typst templates', !!browser],
    ['python + pymupdf', pyCmd ? 'ok' : 'optional', pyCmd ? `${pyCmd} / pymupdf ${pyVer}` : 'page numbers will be skipped; pip install -r scripts/requirements.txt', false],
    ['typst (fallback)', typstBin ? 'available' : 'absent', typstBin || 'optional: needed only when there is no browser', false],
    ['CJK fonts', cjkFaces ? 'ok' : 'unknown', cjkFaces ? `${cjkFaces} Chinese faces` : 'fc-list not available (normal on macOS/Windows)', false],
    ['platform', 'info', `${process.platform} ${process.arch}`, false],
  ];

  const width = Math.max(...rows.map((r) => r[0].length));
  const ready = nodeMajor >= 18 && hasKatexFonts && !!browser;
  console.log('');
  console.log('  md-to-pdf doctor');
  console.log('  ' + '-'.repeat(56));
  for (const [name, state, detail, blocking] of rows) {
    const mark = blocking ? '+' : '-';
    console.log(`  ${mark} ${name.padEnd(width)}  ${String(state).padEnd(10)} ${detail}`);
  }
  console.log('  ' + '-'.repeat(56));
  console.log(ready
    ? '  READY    node scripts/md2pdf.js in.md out.pdf'
    : '  NOT READY   fix the lines above, then run this again');
  if (!browser) console.log('  no browser?   typst compile scripts/typst-template.typ out.pdf');
  console.log('');
  process.exit(ready ? 0 : 1);
}

const [inputMd, outputPdf, titleArg, subtitleArg] = process.argv.slice(2);
if (!inputMd || !outputPdf) {
  console.error('usage: node md2pdf.js <input.md> <output.pdf> [title] [subtitle]');
  console.error('       node md2pdf.js --selftest');
  process.exit(2);
}

const browser = findBrowser();
if (!browser) {
  console.error('No Chromium-based browser found (Edge / Chrome / Chromium).');
  console.error('  - checked: MD2PDF_EDGE, the standard Windows / macOS / Linux locations and $PATH');
  console.error('  - fix one of:');
  console.error('      MD2PDF_EDGE=/path/to/chrome node scripts/md2pdf.js in.md out.pdf');
  console.error('      or compile with the Typst templates instead:');
  console.error('      typst compile scripts/typst-template.typ out.pdf   (see SKILL.md "No Chromium")');
  process.exit(3);
}

const OUTDIR = path.join(__dirname, 'out');
fs.mkdirSync(OUTDIR, { recursive: true });

const katexDist = path.join(__dirname, 'node_modules', 'katex', 'dist');
const fontDst = path.join(OUTDIR, 'katex-fonts');
if (!fs.existsSync(fontDst)) fs.cpSync(path.join(katexDist, 'fonts'), fontDst, { recursive: true });

const title = titleArg || path.basename(inputMd).replace(/\.md$/i, '');
let md = fs.readFileSync(inputMd, 'utf8').replace(/\r\n/g, '\n');

// ---- 0. language: Chinese gets line-oriented layout + 2em indent; English gets
//         normal markdown paragraph merging, justified text and hyphenation ----
const CJK_RE = /[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/g;
const detectLang = (text) => {
  const cjk = (text.match(CJK_RE) || []).length;
  if (!cjk) return 'en';
  const latin = (text.match(/[A-Za-z]/g) || []).length;
  return cjk >= 20 && cjk * 2 >= latin ? 'zh' : 'en';
};
const langEnv = (process.env.MD2PDF_LANG || '').toLowerCase();
const lang = langEnv === 'zh' || langEnv === 'en' ? langEnv : detectLang(md);
const isZh = lang === 'zh';

// ---- 1. extract math BEFORE markdown parsing ----
const inline = [];
const display = [];
md = md.replace(/\\\[([\s\S]*?)\\\]/g, (_m, tex) => {
  display.push(tex.trim());
  return `\n\nZZEQTOKEN${display.length - 1}ZZEQTOKEN\n\n`;
});
md = md.replace(/\\\(([\s\S]*?)\\\)/g, (_m, tex) => {
  inline.push(tex.trim());
  return `ZZINLINEMATH${inline.length - 1}ZZINLINEMATH`;
});

// ---- 2. heading normalisation:  ### -> ## ;  **bold line** -> ### ----
md = md.replace(/^\*\*(.+?)\*\*\s*$/gm, '####$1');
// only demote when the document has no level-2 heading at all (flat one-line reports);
// otherwise a real ### hierarchy would be flattened
if (!/^## /m.test(md)) md = md.replace(/^### /gm, '## ');
md = md.replace(/^####/gm, '### ');

// ---- 2b. line-oriented layout (Chinese reports are written one item per line) ----
if (isZh && process.env.MD2PDF_LINE_ORIENTED !== '0') {
  md = md.split(/\n[ \t]*\n/).map((block) => {
    if (!block.includes('\n') || /^\s*(#|>|\||-|\*|\d+\.)\s/m.test(block)) return block;
    return block.split('\n').map((r) => r.trim()).filter(Boolean).join('\n\n');
  }).join('\n\n');
}

// ---- 3. markdown -> html ----
const mdi = new MarkdownIt({ html: false, linkify: false, typographer: false });
let body = mdi.render(md);

// ---- 4. render math ----
const renderTex = (tex, displayMode) => katex.renderToString(tex, {
  displayMode, throwOnError: false, strict: 'ignore', output: 'html',
});
body = body.replace(/<p>\s*ZZEQTOKEN(\d+)ZZEQTOKEN\s*<\/p>/g,
  (_m, n) => `<div class="eqblock">${renderTex(display[Number(n)], true)}</div>`);
body = body.replace(/ZZINLINEMATH(\d+)ZZINLINEMATH/g,
  (_m, n) => renderTex(inline[Number(n)], false));

const katexCss = fs.readFileSync(path.join(katexDist, 'katex.min.css'), 'utf8')
  .replace(/url\(fonts\//g, 'url(katex-fonts/');

// ---- 5. layout: one recipe, two typographic profiles ----
// Chinese: SimSun/SimHei, 2em first-line indent, no hyphenation needed.
// English: Times-family serif, no indent, justified with hyphenation enabled.
// Ordered so the first hit wins on each OS: macOS ships Songti/PingFang,
// Windows ships SimSun/SimHei, Linux usually has Noto CJK. A buyer on any of
// the three should never see tofu.
const bodyFont = isZh
  ? '"Songti SC","STSong","SimSun","\u5b8b\u4f53","Noto Serif CJK SC","Source Han Serif SC","Noto Serif SC",serif'
  : '"Times New Roman","Liberation Serif","DejaVu Serif","Nimbus Roman",Georgia,serif';
const headFont = isZh
  ? '"PingFang SC","Hiragino Sans GB","Heiti SC","SimHei","\u9ed1\u4f53","Noto Sans CJK SC","Source Han Sans SC","Noto Sans SC",sans-serif'
  : '"Helvetica Neue","Segoe UI",Arial,"Liberation Sans","DejaVu Sans",sans-serif';
const paraIndent = isZh ? '2em' : '0';
const h1Spacing = isZh ? '1px' : '0.2px';
const hyphenCss = isZh ? '' : '  hyphens: auto;\n  -webkit-hyphens: auto;\n';

const css = `
@page { size: A4; margin: 2.4cm 2.5cm 2.2cm 2.6cm; }
* { box-sizing: border-box; }
body { font-family: ${bodyFont}; font-size: 12pt; line-height: 1.72; color: #000;
       text-align: justify; margin: 0;
${hyphenCss}}
h1 { font-family: ${headFont}; font-size: 20pt; font-weight: 700; text-align: center;
     margin: 0 0 4pt 0; letter-spacing: ${h1Spacing}; }
.subtitle { text-align: center; font-size: 12pt; margin: 0 0 5pt 0; }
h2 { font-family: ${headFont}; font-size: 15pt; font-weight: 700; margin: 16pt 0 7pt 0; page-break-after: avoid; }
h3 { font-family: ${headFont}; font-size: 12.5pt; font-weight: 700; margin: 11pt 0 4pt 0; page-break-after: avoid; }
p { margin: 0 0 5pt 0; text-indent: ${paraIndent}; ${isZh ? '' : 'orphans: 2; widows: 2;'} }
table { border-collapse: collapse; margin: 6pt 0; font-size: 10.5pt; }
th, td { border: 0.5pt solid #666; padding: 3pt 5pt; }
pre, code { font-family: Consolas, "DejaVu Sans Mono", monospace; font-size: 10pt; }
pre { background: #f4f4f4; padding: 6pt; white-space: pre-wrap; }
.eqblock { text-align: center; margin: 9pt 0; page-break-inside: avoid; text-indent: 0; }
.katex { font-size: 1.03em; }
.katex-display { margin: 0.25em 0; }
strong { font-family: ${headFont}; }
`;

const html = `<!DOCTYPE html>
<html lang="${isZh ? 'zh-CN' : 'en'}"><head><meta charset="utf-8"><title>${title}</title>
<style>${katexCss}</style><style>${css}</style></head><body>
<h1>${title}</h1>
${subtitleArg ? `<div class="subtitle">${subtitleArg}</div>` : ''}
${body}
</body></html>`;

const htmlPath = path.join(OUTDIR, 'doc.html');
fs.writeFileSync(htmlPath, html, 'utf8');
if (fs.existsSync(outputPdf)) fs.rmSync(outputPdf);
execFileSync(browser, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-pdf-header-footer',
  `--print-to-pdf=${outputPdf}`, 'file:///' + htmlPath.replace(/\\/g, '/')],
  { stdio: 'ignore', timeout: 180000 });
console.log(`PDF -> ${outputPdf}  (lang: ${lang})`);
