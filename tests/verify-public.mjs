import { chromium } from '@playwright/test';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const URL = process.env.GAME_URL || 'https://walkingbad10.github.io/napoli-life-opencode/';
const ROOT = process.cwd();
const SHOTS = join(ROOT, 'screenshots');
mkdirSync(SHOTS, { recursive: true });

const results = [];
const check = (name, ok, detail = '') => {
  results.push({ name, ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ' — ' + detail : ''}`);
  if (!ok) process.exitCode = 1;
};

const localChrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const executablePath = process.env.CHROME_PATH || (existsSync(localChrome) ? localChrome : undefined);
let browser;
try {
  browser = await chromium.launch({
    ...(executablePath ? { executablePath } : {}),
    headless: true,
    args: ['--autoplay-policy=no-user-gesture-required', '--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));

  const response = await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  check('link pubblico raggiungibile', !!response && response.ok(), response ? String(response.status()) : 'no response');
  check('titolo corretto', (await page.title()).includes('NAPOLI LIFE'));
  await page.locator('#start-btn').click();
  await page.waitForFunction(() => window.__napoli?.ready === true, null, { timeout: 45000 });
  await page.waitForTimeout(1200);
  const state = await page.evaluate(() => window.__napoli.state());
  check('versione pubblicata 0.2.0', state.version === '0.2.0', state.version);
  check('canvas presente', await page.locator('#game canvas').count() >= 1);
  await page.keyboard.down('KeyD');
  await page.waitForTimeout(500);
  await page.keyboard.up('KeyD');
  const moved = await page.evaluate(() => window.__napoli.state());
  check('movimento sul sito pubblico', moved.x > state.x + 0.3, `x ${state.x.toFixed(2)} -> ${moved.x.toFixed(2)}`);
  await page.screenshot({ path: join(SHOTS, 'v0.2_public_link.png') });
  check('nessun errore console sul sito pubblico', errors.length === 0, errors.slice(0, 4).join(' | '));

  writeFileSync(join(SHOTS, 'public-link-report.json'), JSON.stringify({
    url: URL,
    checked_utc: new Date().toISOString(),
    results,
    environment: 'Chrome headless — sito pubblico GitHub Pages',
  }, null, 2));
  console.log(`\n${results.filter(r => r.ok).length}/${results.length} controlli superati su ${URL}`);
} catch (e) {
  console.error('VERIFICA LINK FALLITA', e);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
}
