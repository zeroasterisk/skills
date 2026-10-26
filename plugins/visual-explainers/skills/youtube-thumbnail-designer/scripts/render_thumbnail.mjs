#!/usr/bin/env node
/**
 * Programmatic 1920x1080 YouTube Thumbnail & Social Hero Card Renderer
 *
 * Usage:
 *   node render_thumbnail.mjs \
 *     --screenshot ./ui.png \
 *     --eyebrow "TRAVEL UI DEMO" \
 *     --title-top "Audio with" \
 *     --title-gradient "Generative UI" \
 *     --subtitle "A2UI & Gemini 3.8 Live" \
 *     --footer "Speech-to-Speech • Live Surface Streaming" \
 *     --badge "GEMINI 3.8 LIVE VOICE" \
 *     --spotlight "53.8,23.6,30.8,24.5" \
 *     --archetype 1 \
 *     --output ./youtube_thumbnail.png
 */

import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

function parseArgs(argv) {
  const args = {
    screenshot: '',
    eyebrow: 'LIVE DEMO',
    titleTop: 'Next-Gen',
    titleGradient: 'Developer UI',
    subtitle: 'Real-Time Streaming Architecture',
    footer: 'Zero-Latency • Production Ready',
    badge: 'FEATURE SPOTLIGHT',
    spotlight: '', // e.g. "53.8,23.6,30.8,24.5" (left,top,width,height in %)
    aspectRatio: '16 / 9',
    archetype: '1',
    output: 'youtube_thumbnail.png',
  };

  for (let i = 2; i < argv.length; i++) {
    const key = argv[i];
    const val = argv[i + 1];
    if (key === '--screenshot') { args.screenshot = val; i++; }
    else if (key === '--eyebrow') { args.eyebrow = val; i++; }
    else if (key === '--title-top') { args.titleTop = val; i++; }
    else if (key === '--title-gradient') { args.titleGradient = val; i++; }
    else if (key === '--subtitle') { args.subtitle = val; i++; }
    else if (key === '--footer') { args.footer = val; i++; }
    else if (key === '--badge') { args.badge = val; i++; }
    else if (key === '--spotlight') { args.spotlight = val; i++; }
    else if (key === '--aspect-ratio') { args.aspectRatio = val; i++; }
    else if (key === '--archetype') { args.archetype = val; i++; }
    else if (key === '--output') { args.output = val; i++; }
  }
  return args;
}

function findChromeExecutable() {
  const candidates = [
    process.env.CHROME_BIN,
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ].filter(Boolean);

  for (const bin of candidates) {
    if (fs.existsSync(bin)) return bin;
  }
  try {
    const which = execSync('which google-chrome || which chromium', { encoding: 'utf8' }).trim();
    if (which) return which.split('\n')[0];
  } catch {
    // fallback to default playwright browser
  }
  return undefined;
}

async function loadPlaywright() {
  try {
    return await import('playwright');
  } catch {
    // Search common workspace node_modules if invoked from outside a project
    const fallbackPaths = [
      path.resolve(process.cwd(), 'node_modules/playwright/index.mjs'),
    ];
    for (const p of fallbackPaths) {
      if (fs.existsSync(p)) return await import(p);
    }
    throw new Error(
      'Playwright not found. Install via `npm i -D playwright` or run from a workspace with playwright installed.'
    );
  }
}

function buildArchetype1Html(args, dataUri) {
  let spotlightHtml = '';
  if (args.spotlight) {
    const [left, top, width, height] = args.spotlight.split(',').map(s => s.trim());
    spotlightHtml = `
      <div class="live-highlight" style="left:${left}%; top:${top}%; width:${width}%; height:${height}%;">
        <div class="live-highlight-badge">${args.badge}</div>
      </div>`;
  }

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@700;800;900&family=Space+Grotesk:wght@600;700;800&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1920px;
    height: 1080px;
    overflow: hidden;
    background: #050812;
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
    position: relative;
    color: #ffffff;
  }
  .bg-ambient {
    position: absolute;
    inset: -60px;
    background-image: url('${dataUri}');
    background-size: cover;
    background-position: center;
    filter: blur(48px) brightness(0.30) saturate(1.5);
    transform: scale(1.08);
    z-index: 1;
  }
  .showcase-container {
    position: absolute;
    top: 44px;
    right: 42px;
    width: 1375px;
    aspect-ratio: ${args.aspectRatio};
    z-index: 3;
    perspective: 1900px;
  }
  .showcase-frame {
    width: 100%;
    height: 100%;
    border-radius: 22px;
    position: relative;
    transform: rotateY(-7deg) rotateX(2deg) rotateZ(-0.4deg);
    transform-origin: center right;
    box-shadow:
      -35px 35px 95px rgba(0, 0, 0, 0.88),
      0 0 0 2px rgba(148, 163, 184, 0.28),
      0 0 65px rgba(56, 189, 248, 0.28);
    background: #0d1220;
  }
  .showcase-frame img {
    width: 100%;
    height: 100%;
    border-radius: 22px;
    display: block;
    filter: contrast(1.06) brightness(1.05);
  }
  .live-highlight {
    position: absolute;
    border-radius: 16px;
    border: 3.5px solid #38bdf8;
    box-shadow:
      0 0 38px rgba(56, 189, 248, 0.85),
      inset 0 0 28px rgba(56, 189, 248, 0.22);
    pointer-events: none;
    z-index: 6;
  }
  .live-highlight-badge {
    position: absolute;
    top: -19px;
    right: 16px;
    background: linear-gradient(135deg, #0284c7, #7c3aed);
    color: #fff;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 800;
    font-size: 14px;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    padding: 5px 14px;
    border-radius: 999px;
    box-shadow: 0 4px 16px rgba(14, 165, 233, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.55);
  }
  .left-scrim {
    position: absolute;
    inset: 0;
    background: linear-gradient(
      95deg,
      rgba(5, 8, 18, 0.99) 0%,
      rgba(7, 11, 24, 0.97) 37%,
      rgba(9, 14, 29, 0.84) 47%,
      rgba(9, 14, 29, 0.14) 60%,
      rgba(9, 14, 29, 0.0) 100%
    );
    z-index: 4;
  }
  .left-ambient-glow {
    position: absolute;
    inset: 0;
    background:
      radial-gradient(ellipse 650px 550px at 22% 42%, rgba(56, 189, 248, 0.17) 0%, rgba(168, 85, 247, 0.11) 48%, rgba(5, 8, 18, 0) 78%),
      radial-gradient(circle 480px at 12% 82%, rgba(244, 114, 182, 0.12) 0%, transparent 70%);
    z-index: 5;
    pointer-events: none;
  }
  .left-texture {
    position: absolute;
    inset: 0;
    background-image:
      radial-gradient(rgba(148, 163, 184, 0.16) 1.25px, transparent 1.25px),
      linear-gradient(135deg, rgba(56, 189, 248, 0.05) 0%, rgba(168, 85, 247, 0.02) 45%, transparent 65%);
    background-size: 24px 24px, 100% 100%;
    mask-image: linear-gradient(90deg, rgba(0, 0, 0, 0.95) 0%, rgba(0, 0, 0, 0.65) 36%, transparent 54%);
    -webkit-mask-image: linear-gradient(90deg, rgba(0, 0, 0, 0.95) 0%, rgba(0, 0, 0, 0.65) 36%, transparent 54%);
    z-index: 6;
    pointer-events: none;
  }
  .hero-content {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    width: 1050px;
    padding: 84px 0 80px 104px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    z-index: 10;
  }
  .eyebrow-row { display: flex; align-items: center; gap: 18px; }
  .eyebrow-pill {
    display: inline-flex;
    align-items: center;
    gap: 15px;
    padding: 15px 30px;
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.88);
    border: 2.5px solid rgba(56, 189, 248, 0.65);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55), 0 0 28px rgba(56, 189, 248, 0.35);
    backdrop-filter: blur(18px);
  }
  .pulse-dot {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: #38bdf8;
    box-shadow: 0 0 16px #38bdf8, 0 0 30px #38bdf8;
  }
  .eyebrow-text {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 30px;
    font-weight: 800;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    background: linear-gradient(90deg, #38bdf8 0%, #e879f9 55%, #fb7185 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .headline-stack { display: flex; flex-direction: column; gap: 26px; }
  .title-line-1 {
    font-size: 114px;
    font-weight: 900;
    line-height: 0.96;
    letter-spacing: -0.038em;
    color: #ffffff;
    text-shadow: 0 18px 45px rgba(0, 0, 0, 0.78);
  }
  .title-line-1 .gradient-accent {
    display: block;
    margin-top: 6px;
    background: linear-gradient(95deg, #38bdf8 0%, #a855f7 48%, #f472b6 80%, #fb7185 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 10px 32px rgba(168, 85, 247, 0.52));
  }
  .accent-divider {
    width: 210px;
    height: 8px;
    border-radius: 999px;
    background: linear-gradient(90deg, #38bdf8, #a855f7, #ec4899);
    box-shadow: 0 0 28px rgba(168, 85, 247, 0.65);
  }
  .subtitle-card {
    display: inline-flex;
    flex-direction: column;
    gap: 14px;
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.88) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 2px solid rgba(192, 132, 252, 0.58);
    border-left: 9px solid #c084fc;
    border-radius: 24px;
    padding: 26px 40px;
    width: fit-content;
    box-shadow: 0 22px 55px rgba(0, 0, 0, 0.72), 0 0 40px rgba(168, 85, 247, 0.30);
    backdrop-filter: blur(22px);
  }
  .subtitle-text {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 62px;
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -0.022em;
    background: linear-gradient(90deg, #fde047 0%, #f472b6 48%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .audio-footer { display: flex; align-items: center; gap: 24px; }
  .waveform-box {
    display: flex;
    align-items: center;
    gap: 7px;
    background: rgba(15, 23, 42, 0.85);
    border: 1.5px solid rgba(56, 189, 248, 0.45);
    padding: 15px 26px;
    border-radius: 18px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.45);
  }
  .bar {
    width: 6px;
    border-radius: 999px;
    background: linear-gradient(180deg, #38bdf8 0%, #a855f7 100%);
  }
  .footer-tag {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 24px;
    font-weight: 600;
    color: #cbd5e1;
    letter-spacing: 0.02em;
  }
</style>
</head>
<body>
  <div class="bg-ambient"></div>
  <div class="showcase-container">
    <div class="showcase-frame">
      <img src="${dataUri}" alt="Product UI Showcase" />
      ${spotlightHtml}
    </div>
  </div>
  <div class="left-scrim"></div>
  <div class="left-ambient-glow"></div>
  <div class="left-texture"></div>
  <div class="hero-content">
    <div class="eyebrow-row">
      <div class="eyebrow-pill">
        <span class="pulse-dot"></span>
        <span class="eyebrow-text">${args.eyebrow}</span>
      </div>
    </div>
    <div class="headline-stack">
      <h1 class="title-line-1">
        ${args.titleTop}
        <span class="gradient-accent">${args.titleGradient}</span>
      </h1>
      <div class="accent-divider"></div>
      <div class="subtitle-card">
        <div class="subtitle-text">${args.subtitle}</div>
      </div>
    </div>
    <div class="audio-footer">
      <div class="waveform-box">
        <div class="bar" style="height: 18px"></div>
        <div class="bar" style="height: 34px"></div>
        <div class="bar" style="height: 46px"></div>
        <div class="bar" style="height: 24px"></div>
        <div class="bar" style="height: 52px"></div>
        <div class="bar" style="height: 38px"></div>
        <div class="bar" style="height: 22px"></div>
        <div class="bar" style="height: 44px"></div>
        <div class="bar" style="height: 30px"></div>
        <div class="bar" style="height: 16px"></div>
      </div>
      <div class="footer-tag">${args.footer}</div>
    </div>
  </div>
</body>
</html>`;
}

(async () => {
  const args = parseArgs(process.argv);
  if (!args.screenshot || !fs.existsSync(args.screenshot)) {
    console.error('Error: Provide a valid --screenshot <path.png>');
    process.exit(1);
  }

  const imgBase64 = fs.readFileSync(args.screenshot).toString('base64');
  const dataUri = `data:image/png;base64,${imgBase64}`;
  const html = buildArchetype1Html(args, dataUri);

  const { chromium } = await loadPlaywright();
  const executablePath = findChromeExecutable();
  const launchOpts = {
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  };
  if (executablePath) launchOpts.executablePath = executablePath;

  const browser = await chromium.launch(launchOpts);
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
  });

  const page = await context.newPage();
  await page.setContent(html, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: args.output, type: 'png' });
  await browser.close();

  console.log(`Rendered 1920x1080 thumbnail to: ${path.resolve(args.output)}`);
})();
