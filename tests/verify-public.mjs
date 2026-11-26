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
  check('versione pubblicata 0.6.0', state.version === '0.6.0', state.version);
  check('canvas presente', await page.locator('#game canvas').count() >= 1);
  check('vita v0.6 esposta', !!(state.needs && state.home && state.job && state.train && state.open && state.stats &&
    state.vehicles && state.social && state.sectors && state.worldBounds));
  check('HUD bisogni presente', await page.locator('#hud-hunger').isVisible() && await page.locator('#hud-energy').isVisible());
  await page.locator('.ico[data-panel="life"]').click();
  check('pannello Vita pubblico', (await page.locator('#panel-content').innerText()).includes('Vita a Pianura'));
  await page.locator('#panel-close').click();
  await page.locator('.ico[data-panel="vehicles"]').click();
  check('pannello Veicoli pubblico', (await page.locator('#panel-content').innerText()).includes('Concessionaria'));
  await page.locator('#panel-close').click();
  await page.locator('.ico[data-panel="relations"]').click();
  check('pannello Relazioni pubblico', (await page.locator('#panel-content').innerText()).includes('Relazioni'));
  await page.locator('#panel-close').click();
  check('area estesa pubblica', state.worldBounds.maxX === 704 && state.poiSummary.fictional === 2,
    JSON.stringify(state.poiSummary));
  await page.keyboard.down('KeyD');
  await page.waitForTimeout(500);
  await page.keyboard.up('KeyD');
  const moved = await page.evaluate(() => window.__napoli.state());
  check('movimento sul sito pubblico', moved.x > state.x + 0.3, `x ${state.x.toFixed(2)} -> ${moved.x.toFixed(2)}`);
  await page.screenshot({ path: join(SHOTS, 'v0.6_public_link.png') });

  // Qualità minima della build pubblicata: palette ricca e nessuna ombra nera dominante.
  const visual = await page.evaluate(() => {
    const canvas = document.querySelector('#game canvas');
    const { data } = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height);
    const colors = new Set();
    let black = 0, n = 0;
    for (let i = 0; i < data.length; i += 64) {
      colors.add((data[i] << 16) | (data[i + 1] << 8) | data[i + 2]);
      if (data[i] < 8 && data[i + 1] < 8 && data[i + 2] < 8) black++;
      n++;
    }
    return { colors: colors.size, blackRatio: black / n };
  });
  check('schermata pubblica con palette ricca', visual.colors > 120, `${visual.colors} colori`);
  check('nessuna ombra nera dominante sul sito pubblico', visual.blackRatio < 0.02,
    `${(visual.blackRatio * 100).toFixed(2)}%`);
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
