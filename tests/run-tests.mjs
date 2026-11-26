import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = process.cwd();
const URL = 'http://127.0.0.1:4173/';
const SHOTS = join(ROOT, 'screenshots');
mkdirSync(SHOTS, { recursive: true });

const results = [];
function check(name, ok, detail = '') {
  results.push({ name, ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ' — ' + detail : ''}`);
  if (!ok) process.exitCode = 1;
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function waitServer() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(URL);
      if (r.ok) return true;
    } catch { /* server non ancora pronto */ }
    await sleep(500);
  }
  return false;
}

const server = spawn(process.execPath, ['node_modules/vite/bin/vite.js', 'preview', '--host', '127.0.0.1', '--port', '4173'], { cwd: ROOT, stdio: 'ignore' });
let browser;
try {
  check('server di preview available', await waitServer());
  // Browser locale Windows se presente, altrimenti Chromium fornito da Playwright (CI/Linux/macOS).
  const localChrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
  const executablePath = process.env.CHROME_PATH ||
    (existsSync(localChrome) ? localChrome : undefined);
  browser = await chromium.launch({
    ...(executablePath ? { executablePath } : {}),
    headless: true,
    args: ['--autoplay-policy=no-user-gesture-required', '--use-gl=swiftshader', '--no-sandbox'],
  });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));

  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  check('schermata iniziale visibile', await page.locator('#title').isVisible());
  await page.locator('#start-btn').click();
  await page.waitForFunction(() => window.__napoli?.ready === true, null, { timeout: 30000 });
  await sleep(1200);
  const start = await page.evaluate(() => window.__napoli.state());
  check('versione corretta', start.version === '0.3.0', start.version);
  check('canvas WebGL/Canvas presente', await page.locator('#game canvas').count() >= 1);
  await page.screenshot({ path: join(SHOTS, 'v0.3_world_desktop.png') });

  // Controllo qualità dell'immagine direttamente sul canvas di gioco: palette ricca,
  // nessuna dominanza di nero pieno (ombre dure della 0.2.0) e luminosità realistico.
  const visual = await page.evaluate(() => {
    const canvas = document.querySelector('#game canvas');
    const ctx = canvas.getContext('2d');
    const { data } = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const colors = new Set();
    let black = 0, dark = 0, n = 0, luma = 0;
    for (let i = 0; i < data.length; i += 64) {
      const r = data[i], g = data[i + 1], b = data[i + 2];
      colors.add((r << 16) | (g << 8) | b);
      const l = 0.2126 * r + 0.7152 * g + 0.0722 * b;
      if (r < 8 && g < 8 && b < 8) black++;
      if (l < 36) dark++;
      luma += l;
      n++;
    }
    return { colors: colors.size, blackRatio: black / n, darkRatio: dark / n, luma: luma / n,
             w: canvas.width, h: canvas.height };
  });
  // La palette è volutamente ristretta: 120 colori distinti campionati sono già un segnale
  // che la scena non è piatta (la 0.2.0 ne aveva meno di 60 nelle zone ombreggiate).
  check('screenshot: palette pixel ricca', visual.colors > 120, `${visual.colors} colori campionati`);
  check('screenshot: nessuna ombra nera dominante', visual.blackRatio < 0.02, `${(visual.blackRatio * 100).toFixed(2)}% nero`);
  check('screenshot: scena non sottosposta', visual.luma > 55 && visual.luma < 215, `luma ${visual.luma.toFixed(0)}`);

  // Movimento 8 direzioni + corsa
  await page.keyboard.down('KeyD');
  await sleep(650);
  await page.keyboard.up('KeyD');
  const moved = await page.evaluate(() => window.__napoli.state());
  check('movimento destra', moved.x > start.x + 0.4, `x ${start.x.toFixed(2)} -> ${moved.x.toFixed(2)}`);
  await page.keyboard.down('KeyW');
  await sleep(500);
  await page.keyboard.up('KeyW');
  const moved2 = await page.evaluate(() => window.__napoli.state());
  check('movimento alto', moved2.y < moved.y - 0.3, `y ${moved.y.toFixed(2)} -> ${moved2.y.toFixed(2)}`);

  // Missione biglietto: interazione, dialogo, acquisto, salvataggio stato
  await page.evaluate(() => window.__napoli.teleport(-3, -4.6));
  await sleep(250);
  await page.keyboard.press('KeyE');
  await page.waitForSelector('#dialog:not(.hidden)', { timeout: 5000 });
  await page.locator('#dialog-choices button', { hasText: 'Acquista' }).click();
  await sleep(350);
  const afterTicket = await page.evaluate(() => window.__napoli.state());
  check('acquisto biglietto EAV', afterTicket.money < start.money && (afterTicket.inventory.biglietto ?? 0) >= 1,
    `€ ${start.money} -> € ${afterTicket.money}`);
  check('missione biglietto completata', afterTicket.quests.find(q => q.id === 'biglietto')?.done === true);

  // Ingresso della stazione: sulla banchina reale, non sul retro dell'edificio.
  await page.evaluate(() => window.__napoli.teleport(0, -6.1));
  await sleep(250);
  await page.keyboard.press('KeyE');
  await sleep(500);
  check('ingresso nella stazione reale', (await page.evaluate(() => window.__napoli.state())).room === 'station');
  await page.keyboard.press('KeyE');
  await sleep(400);
  check('uscita dalla stazione', (await page.evaluate(() => window.__napoli.state())).room === null);

  // Interno del bar e uscita
  await page.evaluate(() => window.__napoli.teleport(-17, -57.2));
  await sleep(250);
  await page.keyboard.press('KeyE');
  await sleep(600);
  check('ingresso nel bar', (await page.evaluate(() => window.__napoli.state())).room === 'bar');
  await page.screenshot({ path: join(SHOTS, 'v0.3_bar_interior.png') });
  await page.keyboard.press('KeyE');
  await sleep(500);
  check('uscita dal bar', (await page.evaluate(() => window.__napoli.state())).room === null);

  // Menu discreti chiusi di default e funzionanti
  const panelHiddenAtStart = await page.locator('#panel').evaluate(el => el.classList.contains('hidden'));
  check('pannelli chiusi di default', panelHiddenAtStart);
  await page.locator('.ico[data-panel="quests"]').click();
  check('diario missioni visibile', (await page.locator('#panel-content').innerText()).includes('Diario'));
  await page.locator('#panel-close').click();

  // Rotazione: nessun reload, posizione e progressi conservati
  await page.evaluate(() => { window.__rotationMarker = 42; });
  const beforeRotate = await page.evaluate(() => window.__napoli.state());
  await page.setViewportSize({ width: 390, height: 844 });
  await sleep(700);
  const portrait = await page.evaluate(() => ({ state: window.__napoli.state(), marker: window.__rotationMarker,
    w: document.querySelector('#game canvas').width, h: document.querySelector('#game canvas').height }));
  check('portrait: nessun reload', portrait.marker === 42);
  check('portrait: posizione conservata', Math.abs(portrait.state.x - beforeRotate.x) < 0.2 && Math.abs(portrait.state.y - beforeRotate.y) < 0.2);
  check('portrait: canvas adattato', portrait.h > portrait.w, `${portrait.w}x${portrait.h}`);
  await page.screenshot({ path: join(SHOTS, 'v0.3_portrait.png') });

  await page.setViewportSize({ width: 844, height: 390 });
  await sleep(700);
  const landscape = await page.evaluate(() => ({ state: window.__napoli.state(), marker: window.__rotationMarker,
    w: document.querySelector('#game canvas').width, h: document.querySelector('#game canvas').height }));
  check('landscape: nessun reload', landscape.marker === 42);
  check('landscape: posizione conservata', Math.abs(landscape.state.x - portrait.state.x) < 0.2);
  check('landscape: canvas adattato', landscape.w > landscape.h, `${landscape.w}x${landscape.h}`);
  await page.screenshot({ path: join(SHOTS, 'v0.3_landscape.png') });

  // Salvataggio e persistenza
  await page.locator('#save-btn').click();
  await sleep(200);
  const saved = await page.evaluate(() => ({ raw: localStorage.getItem('napoli-life-opencode-save'), state: window.__napoli.state() }));
  check('salvataggio scritto', !!saved.raw && JSON.parse(saved.raw).version === 4);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.locator('#start-btn').click();
  await page.waitForFunction(() => window.__napoli?.ready === true, null, { timeout: 30000 });
  await sleep(600);
  const restored = await page.evaluate(() => window.__napoli.state());
  check('posizione ripristinata', Math.abs(restored.x - saved.state.x) < 0.2, `x ${restored.x.toFixed(2)}`);
  check('progressi ripristinati', restored.quests.find(q => q.id === 'biglietto')?.done === true);

  // Controlli touch presenti
  check('joystick touch presente', await page.locator('#joystick').isVisible());
  check('pulsante corsa presente', await page.locator('#run-btn').isVisible());
  check('pulsante interazione presente', await page.locator('#interact-btn').isVisible());

  check('nessun errore console', errors.length === 0, errors.slice(0, 4).join(' | '));

  writeFileSync(join(SHOTS, 'test-report.json'), JSON.stringify({
    date: new Date().toISOString(), url: URL, results, errors,
    environment: 'Chrome headless (emulazione), Windows — non dispositivo fisico',
  }, null, 2));
  console.log(`\n${results.filter(r => r.ok).length}/${results.length} test superati`);
} catch (e) {
  console.error('TEST FATAL', e);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  server.kill();
}
