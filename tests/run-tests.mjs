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
  const state = () => page.evaluate(() => window.__napoli.state());
  const dialogButton = async text => {
    const btn = page.locator('#dialog-choices button', { hasText: text });
    if (!(await btn.count())) {
      const msg = (await page.locator('#dialog').innerText().catch(() => '(nessun dialogo)')).replace(/\s+/g, ' ').slice(0, 240);
      throw new Error(`Pulsante dialogo mancante: "${text}" — dialogo: ${msg}`);
    }
    await btn.click();
  };

  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  check('schermata iniziale visibile', await page.locator('#title').isVisible());
  await page.locator('#start-btn').click();
  await page.waitForFunction(() => window.__napoli?.ready === true, null, { timeout: 30000 });
  await sleep(1200);
  const start = await state();
  check('versione corretta', start.version === '0.6.0', start.version);
  check('canvas WebGL/Canvas presente', await page.locator('#game canvas').count() >= 1);
  await page.screenshot({ path: join(SHOTS, 'v0.6_world_desktop.png') });

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
  check('screenshot: palette pixel ricca', visual.colors > 120, `${visual.colors} colori campionati`);
  check('screenshot: nessuna ombra nera dominante', visual.blackRatio < 0.02, `${(visual.blackRatio * 100).toFixed(2)}% nero`);
  check('screenshot: scena non sottosposta', visual.luma > 55 && visual.luma < 215, `luma ${visual.luma.toFixed(0)}`);

  // Movimento 8 direzioni + corsa
  await page.keyboard.down('KeyD');
  await sleep(650);
  await page.keyboard.up('KeyD');
  const moved = await state();
  check('movimento destra', moved.x > start.x + 0.4, `x ${start.x.toFixed(2)} -> ${moved.x.toFixed(2)}`);
  await page.keyboard.down('KeyW');
  await sleep(500);
  await page.keyboard.up('KeyW');
  const moved2 = await state();
  check('movimento alto', moved2.y < moved.y - 0.3, `y ${moved.y.toFixed(2)} -> ${moved2.y.toFixed(2)}`);

  // Missione biglietto: interazione, dialogo, acquisto, salvataggio stato
  await page.evaluate(() => window.__napoli.teleport(-3, -4.6));
  await sleep(250);
  await page.keyboard.press('KeyE');
  await page.waitForSelector('#dialog:not(.hidden)', { timeout: 5000 });
  await dialogButton('Acquista');
  await sleep(350);
  const afterTicket = await state();
  check('acquisto biglietto EAV', afterTicket.money < start.money && (afterTicket.inventory.biglietto ?? 0) >= 1,
    `€ ${start.money} -> € ${afterTicket.money}`);
  check('missione biglietto completata', afterTicket.quests.find(q => q.id === 'biglietto')?.done === true);

  // Ingresso della stazione: sulla banchina reale, non sul retro dell'edificio.
  await page.evaluate(() => window.__napoli.teleport(0, -6.1));
  await sleep(350);
  await page.screenshot({ path: join(SHOTS, 'v0.6_station_exterior.png') });
  await page.keyboard.press('KeyE');
  await sleep(500);
  check('ingresso nella stazione reale', (await state()).room === 'station');
  await page.screenshot({ path: join(SHOTS, 'v0.6_station_interior.png') });
  await page.keyboard.press('KeyE');
  await sleep(400);
  check('uscita dalla stazione', (await state()).room === null);

  // Interno del bar e uscita
  await page.evaluate(() => window.__napoli.teleport(-17, -57.2));
  await sleep(250);
  await page.keyboard.press('KeyE');
  await sleep(600);
  check('ingresso nel bar', (await state()).room === 'bar');
  await page.screenshot({ path: join(SHOTS, 'v0.6_bar_interior.png') });
  await page.keyboard.press('KeyE');
  await sleep(500);
  check('uscita dal bar', (await state()).room === null);

  // Menu discreti chiusi di default e funzionanti
  const panelHiddenAtStart = await page.locator('#panel').evaluate(el => el.classList.contains('hidden'));
  check('pannelli chiusi di default', panelHiddenAtStart);
  await page.locator('.ico[data-panel="quests"]').click();
  check('diario missioni visibile', (await page.locator('#panel-content').innerText()).includes('Diario'));
  await page.locator('#panel-close').click();

  // Rotazione: nessun reload, posizione e progressi conservati
  await page.evaluate(() => { window.__rotationMarker = 42; });
  const beforeRotate = await state();
  await page.setViewportSize({ width: 390, height: 844 });
  await sleep(700);
  const portrait = await page.evaluate(() => ({ state: window.__napoli.state(), marker: window.__rotationMarker,
    w: document.querySelector('#game canvas').width, h: document.querySelector('#game canvas').height }));
  check('portrait: nessun reload', portrait.marker === 42);
  check('portrait: posizione conservata', Math.abs(portrait.state.x - beforeRotate.x) < 0.2 && Math.abs(portrait.state.y - beforeRotate.y) < 0.2);
  check('portrait: canvas adattato', portrait.h > portrait.w, `${portrait.w}x${portrait.h}`);
  await page.screenshot({ path: join(SHOTS, 'v0.6_portrait.png') });

  await page.setViewportSize({ width: 844, height: 390 });
  await sleep(700);
  const landscape = await page.evaluate(() => ({ state: window.__napoli.state(), marker: window.__rotationMarker,
    w: document.querySelector('#game canvas').width, h: document.querySelector('#game canvas').height }));
  check('landscape: nessun reload', landscape.marker === 42);
  check('landscape: posizione conservata', Math.abs(landscape.state.x - portrait.state.x) < 0.2);
  check('landscape: canvas adattato', landscape.w > landscape.h, `${landscape.w}x${landscape.h}`);
  await page.screenshot({ path: join(SHOTS, 'v0.6_landscape.png') });

  // Salvataggio e persistenza
  await page.locator('#save-btn').click();
  await sleep(200);
  const saved = await page.evaluate(() => ({ raw: localStorage.getItem('napoli-life-opencode-save'), state: window.__napoli.state() }));
  check('salvataggio scritto', !!saved.raw && JSON.parse(saved.raw).version === 6);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.locator('#start-btn').click();
  await page.waitForFunction(() => window.__napoli?.ready === true, null, { timeout: 30000 });
  await sleep(600);
  const restored = await state();
  check('posizione ripristinata', Math.abs(restored.x - saved.state.x) < 0.2, `x ${restored.x.toFixed(2)}`);
  check('progressi ripristinati', restored.quests.find(q => q.id === 'biglietto')?.done === true);

  // Controlli touch presenti
  check('joystick touch presente', await page.locator('#joystick').isVisible());
  check('pulsante corsa presente', await page.locator('#run-btn').isVisible());
  check('pulsante interazione presente', await page.locator('#interact-btn').isVisible());

  // ---------------- v0.5.0: vita quotidiana ----------------
  const v5 = await state();
  check('campi v0.5 esposti', !!v5.needs && !!v5.home && !!v5.job && !!v5.train && !!v5.open && !!v5.stats);
  check('orari e pizzeria OSM esposti', Object.keys(v5.open).includes('pizzeria') && v5.open.pizzeria === false);

  // Bisogni: calo graduale, non bloccante.
  await page.evaluate(() => { window.__napoli.setNeeds({ hunger: 80, energy: 80 }); window.__napoli.setTime(9 * 60, 1); });
  const needsBefore = (await state()).needs;
  await sleep(1300);
  const needsAfter = (await state()).needs;
  check('fame ed energia calano con il tempo', needsAfter.hunger < needsBefore.hunger && needsAfter.energy < needsBefore.energy,
    `${needsBefore.hunger}->${needsAfter.hunger} · ${needsBefore.energy}->${needsAfter.energy}`);

  // Orari: il bar è chiuso alle 22:00 e si apre alle 07:00.
  await page.evaluate(() => window.__napoli.setTime(22 * 60));
  check('bar chiuso alle 22:00', (await state()).open.bar === false);
  await page.evaluate(() => window.__napoli.teleport(-17, -57.2));
  await sleep(250);
  await page.keyboard.press('KeyE');
  await sleep(400);
  check('ingresso bloccato a bar chiuso', (await state()).room === null);

  await page.evaluate(() => window.__napoli.setTime(10 * 60));
  await page.keyboard.press('KeyE');
  await sleep(500);
  check('bar aperto alle 10:00', (await state()).room === 'bar');
  await page.evaluate(() => window.__napoli.teleportRoom(164, 120));
  await page.keyboard.press('KeyE');
  await page.waitForSelector('#dialog:not(.hidden)', { timeout: 5000 });
  const beforeCoffee = await state();
  await dialogButton('Un espresso');
  await sleep(350);
  const afterCoffee = await state();
  check('acquisto espresso e sazietà', (afterCoffee.inventory.caffe ?? 0) > (beforeCoffee.inventory.caffe ?? 0) &&
    afterCoffee.needs.hunger > beforeCoffee.needs.hunger, `sazietà ${beforeCoffee.needs.hunger} -> ${afterCoffee.needs.hunger}`);
  await page.locator('.ico[data-panel="inventory"]').click();
  await page.locator('#panel-content button[data-act^="eat:"]').first().click();
  await sleep(250);
  check('consumo dall’inventario', ((await state()).inventory.caffe ?? 0) < (afterCoffee.inventory.caffe ?? 0));
  await page.locator('#panel-close').click();
  await page.evaluate(() => window.__napoli.interact('bar_exit'));
  await sleep(300);
  check('uscita dal bar dopo acquisto', (await state()).room === null);

  // Casa: riposo e arredi persistenti.
  await page.evaluate(() => { window.__napoli.setTime(11 * 60); window.__napoli.setNeeds({ energy: 20 }); window.__napoli.teleport(-0.75, 100.2); });
  await sleep(250);
  await page.keyboard.press('KeyE');
  await sleep(450);
  check('ingresso nella casa personale', (await state()).room === 'home');
  await page.screenshot({ path: join(SHOTS, 'v0.6_home_interior.png') });
  await page.evaluate(() => window.__napoli.interact('bed'));
  await sleep(350);
  const rested = await state();
  check('riposo: orologio avanza e energia torna', rested.time.minute >= 780 && rested.time.minute <= 783 && rested.needs.energy > 60,
    `${rested.clock}, energia ${rested.needs.energy}`);
  await page.evaluate(() => window.__napoli.interact('wardrobe'));
  await page.waitForSelector('#dialog:not(.hidden)', { timeout: 5000 });
  await dialogButton('Compra libreria');
  await sleep(300);
  check('arredo acquistato e salvato', (await state()).home.furniture.bookshelf === true);
  await page.screenshot({ path: join(SHOTS, 'v0.6_home_furnished.png') });
  await page.evaluate(() => window.__napoli.interact('home_exit'));
  await sleep(300);

  // Pizzeria reale OSM (Carpe Diem) + lavoro retribuito.
  await page.evaluate(() => { window.__napoli.setMoney(60); window.__napoli.setTime(13 * 60); window.__napoli.teleport(-126.3, 123.9); });
  await sleep(250);
  await page.keyboard.press('KeyE');
  await sleep(500);
  check('ingresso nella pizzeria Carpe Diem', (await state()).room === 'pizzeria');
  await page.screenshot({ path: join(SHOTS, 'v0.6_pizzeria_interior.png') });
  await page.evaluate(() => window.__napoli.interact('pizzaiolo'));
  await page.waitForSelector('#dialog:not(.hidden)', { timeout: 5000 });
  await dialogButton('Aiuta in pizzeria');
  await sleep(250);
  check('turno di lavoro accettato', (await state()).job.active === 'pizzeria');
  for (let i = 0; i < 3; i++) {
    await page.evaluate(() => window.__napoli.interact('pizza_counter'));
    await page.waitForSelector('#dialog:not(.hidden)', { timeout: 5000 });
    await dialogButton('Compra (€ 4,50)');
    await sleep(250);
  }
  const afterJob = await state();
  check('lavoro completato e retribuito', afterJob.job.progress === 3 && afterJob.stats.jobs >= 1 && afterJob.money > 64,
    `€ ${afterJob.money}, lavori ${afterJob.stats.jobs}`);
  check('pizze acquistate', (afterJob.inventory.pizza ?? 0) >= 3);
  await page.evaluate(() => window.__napoli.interact('pizza_exit'));
  await sleep(300);

  // Treno EAV utilizzabile: biglietto valido, imbarco, guida, sbarco.
  await page.evaluate(() => { window.__napoli.setTime(14 * 60); window.__napoli.teleport(-3, -4.6); });
  await sleep(250);
  await page.keyboard.press('KeyE');
  await page.waitForSelector('#dialog:not(.hidden)', { timeout: 5000 });
  await dialogButton('Acquista');
  await sleep(250);
  const ticketValid = await state();
  check('biglietto EAV con scadenza 90 minuti', ticketValid.train.ticketUntil >= ticketValid.time.absolute);
  // La banchina è in x≈0: cerco il progresso del binario OSM che porta il treno davanti alla porta.
  await page.evaluate(() => {
    // Il tracciato esteso ha segmenti lunghi: 8 m bastano per essere in banchina (soglia 20 m).
    for (let t = 0; t < 1; t += 0.001) {
      window.__napoli.setTrain(t);
      if (Math.abs(window.__napoli.state().train.x) < 8) break;
    }
    window.__napoli.teleport(0, -5);
  });
  await sleep(250);
  await page.keyboard.press('KeyE');
  await page.waitForSelector('#dialog:not(.hidden)', { timeout: 5000 });
  await dialogButton('Guida il treno');
  await sleep(300);
  const boarding = await state();
  check('imbarco sul treno EAV', boarding.train.riding === true && (boarding.inventory.biglietto ?? 0) === 0);
  await page.keyboard.down('KeyD');
  await sleep(900);
  await page.keyboard.up('KeyD');
  const riding = await state();
  // Il binario OSM in banchina è quasi nord-sud: misuro la distanza 2D, non solo x.
  const rideDistance = Math.hypot(riding.train.x - boarding.train.x, riding.train.y - boarding.train.y);
  check('treno guidabile', rideDistance > 0.5,
    `(${boarding.train.x.toFixed(1)}, ${boarding.train.y.toFixed(1)}) -> (${riding.train.x.toFixed(1)}, ${riding.train.y.toFixed(1)}) = ${rideDistance.toFixed(2)} m`);
  await page.screenshot({ path: join(SHOTS, 'v0.6_train_ride.png') });
  await page.keyboard.press('KeyE');
  await page.waitForSelector('#dialog:not(.hidden)', { timeout: 5000 });
  await dialogButton('Scendi a Pianura');
  await sleep(300);
  const offTrain = await state();
  check('sbarco e viaggio registrato', offTrain.train.riding === false && offTrain.stats.rides >= 1 && offTrain.room === null);

  // Audio ambientale a zone e salvataggio schema v6.
  const audio = (await state()).audio;
  check('audio ambientale attivo', audio.started && audio.loops.length >= 4 && audio.sfxCount > 0,
    `${audio.loops.length} loop · ${audio.sfxCount} effetti`);
  await page.locator('#save-btn').click();
  await sleep(200);
  const v6Save = await page.evaluate(() => JSON.parse(localStorage.getItem('napoli-life-opencode-save')));
  check('salvataggio v6 completo', v6Save.version === 6 && !!v6Save.needs && !!v6Save.home && !!v6Save.job &&
    !!v6Save.train && !!v6Save.stats && !!v6Save.vehicles && !!v6Save.social);

  // Compatibilità: un salvataggio v0.5 viene migrato senza perdere denaro e missioni.
  const legacy = await page.evaluate(() => {
    const old = JSON.parse(localStorage.getItem('napoli-life-opencode-save'));
    old.version = 5;
    delete old.vehicles; delete old.social;
    localStorage.setItem('napoli-life-opencode-save', JSON.stringify(old));
    return { money: old.money, ticketDone: old.quests.some(q => q.id === 'biglietto' && q.done) };
  });
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.locator('#start-btn').click();
  await page.waitForFunction(() => window.__napoli?.ready === true, null, { timeout: 30000 });
  await sleep(600);
  const migrated = await state();
  check('migrazione v5 → v6 senza perdite', migrated.money === legacy.money && migrated.quests.find(q => q.id === 'biglietto')?.done === legacy.ticketDone &&
    !!migrated.needs && !!migrated.home && !!migrated.job && !!migrated.train && !!migrated.vehicles && !!migrated.social,
    `€ ${migrated.money}`);

  // ---------------- v0.6.0: area estesa, veicoli, relazioni, streaming ----------------
  const v6 = await state();
  check('bounds rettangolari v0.6', v6.worldBounds.minX === -256 && v6.worldBounds.minY === -320 &&
    v6.worldBounds.maxX === 704 && v6.worldBounds.maxY === 704, JSON.stringify(v6.worldBounds));
  check('POI OSM estesi e attività fittizie dichiarate', v6.poiSummary.total > 40 &&
    v6.poiSummary.shops >= 10 && v6.poiSummary.fictional === 2 && v6.poiSummary.railRoute >= 6,
    JSON.stringify(v6.poiSummary));
  check('settori iniziali caricati', v6.sectors.loaded >= 4 && v6.sectors.total === 240,
    JSON.stringify(v6.sectors));

  // Teleport in una zona distante: il streaming deve caricare nuovi settori senza errori.
  await page.evaluate(() => window.__napoli.teleport(600, 600));
  await sleep(1800);
  const far = await state();
  check('streaming area distante', Math.abs(far.x - 600) < 1 && far.sectors.loaded >= 4 && far.sectors.pending === 0,
    JSON.stringify(far.sectors));
  await page.screenshot({ path: join(SHOTS, 'v0.6_expanded_area.png') });

  // Veicoli: acquisto, guida con collisioni, carburante, discesa.
  await page.evaluate(() => { window.__napoli.setMoney(3000); window.__napoli.buyVehicle('motorcycle'); });
  await sleep(600);
  const bought = await state();
  check('acquisto motocicletta', bought.vehicles.owned.includes('motorcycle') && bought.driving === true);
  await page.keyboard.down('KeyD');
  await sleep(900);
  await page.keyboard.up('KeyD');
  const driven = await state();
  check('guida e carburante', Math.hypot(driven.x - bought.x, driven.y - bought.y) > 0.5 &&
    driven.vehicles.fuel < bought.vehicles.fuel, `${driven.vehicles.fuel.toFixed(1)}%`);
  await page.screenshot({ path: join(SHOTS, 'v0.6_vehicle.png') });
  await page.evaluate(() => window.__napoli.dismountVehicle());
  await sleep(300);
  check('discesa dal veicolo', (await state()).driving === false && (await state()).vehicles.active === null);

  // Relazioni: un regalo al giorno, crescita dell'amicizia.
  await page.evaluate(() => { window.__napoli.giveItem('fiore', 2); window.__napoli.gift('npc1', 'fiore'); });
  await sleep(250);
  const social = await state();
  const rel = social.social.find(r => r.id === 'npc1');
  check('relazione con regalo', !!rel && rel.gifts === 1 && rel.friendship >= 12 && rel.level !== 'conoscente',
    JSON.stringify(rel));
  const secondGift = await page.evaluate(() => window.__napoli.gift('npc1', 'fiore'));
  check('un solo regalo al giorno', secondGift === false);

  // Interni nuovi: almeno tre porte reali raggiungibili dai POI OSM.
  const newDoors = v6.interactables.filter(it => /^(supermarket|tobacco|bookmaker|bakery|clothing|workshop)_door_/.test(it.id));
  check('porte delle nuove attività sui POI', newDoors.length >= 3, `${newDoors.length} porte`);
  if (newDoors.length) {
    const door = newDoors[0];
    const roomName = door.id.split('_door_')[0];
    await page.evaluate(d => window.__napoli.teleport(d.x / 16, d.y / 16), door);
    await sleep(350);
    await page.keyboard.press('KeyE');
    await sleep(600);
    check('ingresso in attività v0.6', (await state()).room === roomName, ` stanza ${roomName}`);
    await page.screenshot({ path: join(SHOTS, 'v0.6_new_interior.png') });
    await page.evaluate(() => window.__napoli.leaveRoom());
    await sleep(250);
  }

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
