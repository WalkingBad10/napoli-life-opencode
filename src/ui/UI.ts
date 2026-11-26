import Phaser from 'phaser';
import { BUILD_ID, BUSINESS_HOURS, MENU, SAVE_VERSION, SERVICE_PRICES, VERSION, WORLD_BOUNDS } from '../config';
import { QUEST_DEFS } from '../systems/QuestSystem';
import { VEHICLE_DEFS, type VehicleKind } from '../systems/VehicleSystem';
import type { NeedsState, WorldData } from '../types';

type Choice = { label: string; action: () => void };

const $ = (id: string) => document.getElementById(id)!;

/** Interfaccia HTML discreta: icone piccole, pannelli chiusi di default, touch responsive. */
export class UI {
  private panelOpen = '';
  private dialogOpen = false;
  private world: WorldData | null = null;
  private toastTimer: number | null = null;
  private mapTimer = 0;

  constructor(private scene: Phaser.Scene) {
    document.querySelectorAll<HTMLButtonElement>('.ico[data-panel]').forEach(btn => {
      btn.addEventListener('click', () => this.openPanel(btn.dataset.panel!));
    });
    $('panel-close').addEventListener('click', () => this.closePanels());
    $('save-btn').addEventListener('click', () => {
      (this.scene as any).manualSave?.();
      this.toast('Partita salvata');
    });
    this.setupTouch();
  }

  private setupTouch(): void {
    const stick = $('joystick');
    const knob = $('joystick-knob');
    let active = false;
    const update = (e: PointerEvent) => {
      const r = stick.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      let dx = (e.clientX - cx) / (r.width / 2);
      let dy = (e.clientY - cy) / (r.height / 2);
      const len = Math.hypot(dx, dy);
      if (len > 1) { dx /= len; dy /= len; }
      knob.style.transform = `translate(${dx * 26}px, ${dy * 26}px)`;
      (this.scene as any).inputSystem?.setTouch(dx, dy);
    };
    stick.addEventListener('pointerdown', e => {
      active = true; stick.setPointerCapture(e.pointerId); update(e);
    });
    stick.addEventListener('pointermove', e => { if (active) update(e); });
    const release = () => {
      active = false;
      knob.style.transform = 'translate(0px, 0px)';
      (this.scene as any).inputSystem?.setTouch(0, 0);
    };
    stick.addEventListener('pointerup', release);
    stick.addEventListener('pointercancel', release);

    const run = $('run-btn');
    const pressRun = (down: boolean) => {
      (this.scene as any).inputSystem && ((this.scene as any).inputSystem.touchRun = down);
      run.style.background = down ? 'rgba(226,184,60,.9)' : '';
    };
    run.addEventListener('pointerdown', e => { e.preventDefault(); pressRun(true); });
    run.addEventListener('pointerup', () => pressRun(false));
    run.addEventListener('pointercancel', () => pressRun(false));

    $('interact-btn').addEventListener('pointerdown', e => {
      e.preventDefault();
      window.dispatchEvent(new Event('napoli-interact'));
    });
  }

  setWorld(world: WorldData): void { this.world = world; }

  toast(text: string): void {
    const el = $('toast');
    el.textContent = text;
    el.classList.remove('hidden');
    if (this.toastTimer) window.clearTimeout(this.toastTimer);
    this.toastTimer = window.setTimeout(() => el.classList.add('hidden'), 2800);
  }

  setHUD(clock: string, money: number, needs?: NeedsState, status?: string,
         homeOwned = true, jobLabel = '', jobProgress = ''): void {
    $('hud-clock').textContent = clock;
    $('hud-money').textContent = `€ ${money.toFixed(2).replace('.', ',')}`;
    if (needs) {
      const hunger = Math.max(0, Math.min(100, needs.hunger));
      const energy = Math.max(0, Math.min(100, needs.energy));
      $('hud-hunger-fill').style.width = `${hunger}%`;
      $('hud-energy-fill').style.width = `${energy}%`;
      $('hud-needs').textContent = status ?? '';
      $('hud-hunger').title = `Sazietà ${Math.round(hunger)}/100`;
      $('hud-energy').title = `Energia ${Math.round(energy)}/100`;
    }
    $('hud-home').textContent = homeOwned ? '🏠' : '';
    $('hud-job').textContent = jobLabel ? `${jobLabel} ${jobProgress}` : '';
  }

  showDialog(speaker: string, text: string, choices: Choice[] = []): void {
    this.dialogOpen = true;
    (this.scene as any).inputSystem && ((this.scene as any).inputSystem.enabled = false);
    $('dialog-speaker').textContent = speaker;
    $('dialog-text').textContent = text;
    const box = $('dialog-choices');
    box.innerHTML = '';
    if (choices.length === 0) choices = [{ label: 'Continua', action: () => this.hideDialog() }];
    for (const c of choices) {
      const b = document.createElement('button');
      b.textContent = c.label;
      b.addEventListener('click', () => { this.hideDialog(); c.action(); });
      box.appendChild(b);
    }
    $('dialog').classList.remove('hidden');
  }

  hideDialog(): void {
    this.dialogOpen = false;
    const input: any = (this.scene as any).inputSystem;
    if (input) { input.enabled = true; input.clearPending?.(); }
    $('dialog').classList.add('hidden');
  }

  isDialogOpen(): boolean { return this.dialogOpen; }
  isPanelOpen(): boolean { return !!this.panelOpen; }
  closePanels(): void { this.panelOpen = ''; $('panel').classList.add('hidden'); }

  update(delta: number): void {
    this.mapTimer -= delta;
    if (this.panelOpen === 'map' && this.mapTimer <= 0) {
      this.mapTimer = 1200;
      this.renderMap();
    }
  }

  openPanel(type: string): void {
    if (this.panelOpen === type) { this.closePanels(); return; }
    this.panelOpen = type;
    $('panel').classList.remove('hidden');
    const content = $('panel-content');
    const s: any = (this.scene as any).save;
    switch (type) {
      case 'map': {
        content.innerHTML = '<h2>Mappa di Pianura</h2><canvas id="minimap" width="320" height="320"></canvas><p class="tag">Dati OSM reali · 960 × 1024 m · settori 64 m caricati in streaming</p><p>Stazione in giallo, tu in blu, negozi reali in blu scuro e attività fittizie in oro. Via Nelson Mandela, Via Provinciale Napoli e Via Montagna Spaccata sono nel riquadro.</p>';
        this.renderMap();
        break;
      }
      case 'inventory': {
        const entries = Object.entries(s.inventory as Record<string, number>);
        content.innerHTML = `<h2>Inventario</h2>${entries.length ? entries.map(([k, v]) => {
          const eatable = !!MENU[k];
          return `<span class="tag">${this.itemName(k)} × ${v}</span>${eatable ? `<button data-act="eat:${k}">Consuma</button>` : ''}`;
        }).join('') : '<p>Zaino vuoto. Il quartiere ti aspetta.</p>'}`;
        break;
      }
      case 'quests': {
        content.innerHTML = '<h2>Diario delle missioni</h2>' + QUEST_DEFS.map(def => {
          const q = (this.scene as any).quests.get(def.id);
          const label = q?.done ? 'COMPLETATA' : q?.accepted ? `${q.progress}/${def.steps.length}` : 'NON ACCETTATA';
          return `<div class="quest ${q?.done ? 'done' : ''}"><b>${def.title}</b><small>${def.description}</small><small>Obiettivo: ${label} · Ricompensa € ${def.reward.toFixed(2)}</small></div>`;
        }).join('');
        break;
      }
      case 'phone': {
        const scene: any = this.scene;
        const clock = scene.clock?.clock ?? '--:--';
        const hours = Object.entries(BUSINESS_HOURS).map(([id, h]) => {
          const open = scene.business?.isOpen(id, scene.clock?.minute ?? 420);
          return `<div class="quest ${open ? 'done' : ''}"><b>${h.label}</b><small>${scene.business?.hoursLabel(id) ?? ''} · ${open ? 'APERTO' : 'CHIUSO'}</small></div>`;
        }).join('');
        content.innerHTML = `<h2>Telefono</h2><p><b>${clock}</b> · Giorno ${scene.clock?.day ?? 1}</p>
          <p>📞 EAV Circumflegrea: 800 001 788</p><p>📞 Bar Pianura: 081 000 0000</p>
          <h3>Orari del quartiere</h3>${hours}
          <p class="tag">Orari simulati: OSM non riporta opening_hours</p>`;
        break;
      }
      case 'wallet': {
        content.innerHTML = `<h2>Portafoglio</h2><p><b>€ ${Number(s.money).toFixed(2).replace('.', ',')}</b></p>
          <p>Hai comprato: ${Object.entries(s.inventory).filter(([k]) => k !== 'parcel' && k !== 'keys').map(([k]) => this.itemName(k)).join(', ') || 'nulla'}</p>
          <p>Abitazione: ${s.home?.owned ? 'di tua proprietà' : 'in affitto'} · seconda casa: ${s.home?.secondHome ? 'acquistata' : 'no'}</p>
          ${s.home?.secondHome ? '' : `<button data-act="home:second">Compra seconda casa (€ ${SERVICE_PRICES.secondHome.toFixed(2)})</button>`}
          <button data-act="export">Esporta salvataggio</button><button data-act="import">Importa salvataggio</button>`;
        break;
      }
      case 'profile': {
        const looks = ['player', 'resident', 'worker', 'teen', 'elderly', 'railway', 'pizzaiolo'];
        content.innerHTML = `<h2>Profilo</h2><p>Aspetto del protagonista</p>${looks.map(l => `<button data-act="look:${l}">${this.lookName(l)}</button>`).join('')}
          <p class="tag">Passi: ${s.stats.steps} · Caffè: ${s.stats.coffees} · Biglietti: ${s.stats.tickets} · Pizze: ${s.stats.pizzas ?? 0} · Viaggi: ${s.stats.rides ?? 0} · Lavori: ${s.stats.jobs ?? 0}</p>`;
        break;
      }
      case 'life': {
        const n = s.needs ?? { hunger: 100, energy: 100 };
        const j = s.job ?? { active: null };
        const h = s.home ?? { owned: true, furniture: {} };
        const train = s.train ?? { ticketUntil: 0 };
        const clock: any = this.scene;
        const valid = clock?.clock && clock.clock.absoluteMinute <= train.ticketUntil;
        content.innerHTML = `<h2>Vita a Pianura</h2>
          <div class="quest"><b>Sazietà</b><small>${Math.round(n.hunger)}/100 · scende lentamente con il tempo</small></div>
          <div class="quest"><b>Energia</b><small>${Math.round(n.energy)}/100 · recupera dormendo a casa</small></div>
          <div class="quest"><b>Lavoro</b><small>${j.active ? `${j.active}: ${j.progress}/${j.target}` : 'Nessun turno attivo'}</small></div>
          <div class="quest"><b>Casa</b><small>${h.owned ? 'Posseduta' : 'Non posseduta'} · libreria ${h.furniture?.bookshelf ? 'sì' : 'no'} · pianta ${h.furniture?.plant ? 'sì' : 'no'}</small></div>
          <div class="quest"><b>Biglietto EAV</b><small>${valid ? `valido fino alle ${this.minuteLabel(train.ticketUntil)}` : 'nessun biglietto valido'}</small></div>
          <div class="quest"><b>Veicoli</b><small>${(s.vehicles?.owned ?? []).length} posseduti · carburante ${Math.round(s.vehicles?.fuel ?? 0)}%</small></div>
          <div class="quest"><b>Abitazione extra</b><small>${h.secondHome ? 'seconda casa disponibile' : 'non acquistata'}</small></div>
          <p class="tag">Mangia al bar, alla pizzeria o al negozio; dormi nel letto di casa. Nuove attività: Via Nelson Mandela, Conad/Coop, forni, tabaccherie e officine.</p>`;
        break;
      }
      case 'relations': {
        const scene: any = this.scene;
        const rels: [string, any][] = scene.social?.all() ?? [];
        const names: Record<string, string> = {
          npc1: 'Antonio, il barista', npc2: 'Rosa, la commerciante', npc3: 'Il signore con il cane',
          npc4: 'Pendolare EAV', npc5: 'Maria, la vicina', npc6: 'Lavoratore',
          npc7: 'Ragazzo con lo scooter', npc8: 'Signora con la borsa',
        };
        const rows = rels.length ? rels.map(([id, r]) => `<div class="quest"><b>${names[id] ?? id}</b><small>${scene.social.level(id)} · amicizia ${Math.round(r.friendship)}/100 · affetto ${Math.round(r.romance)}/100 · regali ${r.gifts}</small><button data-act="gift:${id}:fiore">Regala fiore</button><button data-act="gift:${id}:libro">Regala libro</button></div>`).join('')
          : '<p>Parla con i residenti: qui compariranno le vostre relazioni. Un fiore o un libro li farà sentire più vicini.</p>';
        content.innerHTML = `<h2>Relazioni</h2>${rows}<p class="tag">Un regalo al giorno per persona. Fiore € ${SERVICE_PRICES.giftFlower.toFixed(2)} · libro € ${SERVICE_PRICES.giftBook.toFixed(2)}</p>`;
        break;
      }
      case 'vehicles': {
        const v = s.vehicles ?? { owned: [], active: null, fuel: 0 };
        const scene: any = this.scene;
        const owned = (v.owned as string[]).map(kind => `<div class="quest"><b>${VEHICLE_DEFS[kind as VehicleKind]?.name ?? kind}</b><small>${v.active === kind ? 'IN USO' : 'parcheggiato'}</small><button data-act="vehicle:mount:${kind}">Guida</button></div>`).join('');
        const shop = (Object.entries(VEHICLE_DEFS) as [VehicleKind, typeof VEHICLE_DEFS[VehicleKind]][]).map(([kind, def]) =>
          `<button data-act="vehicle:buy:${kind}">${def.name} — € ${def.price.toFixed(2)}</button>`).join('');
        content.innerHTML = `<h2>Veicoli</h2><p>Carburante: <b>${Math.round(v.fuel ?? 0)}%</b> · ${scene.driving ? 'stai guidando' : 'a piedi'}</p>
          ${owned || '<p>Nessun veicolo posseduto. Visita la concessionaria o acquista qui.</p>'}
          <h3>Concessionaria</h3>${shop}
          <button data-act="vehicle:refuel">Rifornisci (€ ${SERVICE_PRICES.refuel.toFixed(2)})</button>
          <button data-act="vehicle:dismount">Scendi dal veicolo</button>
          <p class="tag">Guida con WASD/frecce · E per scendere. Le auto seguono le collisioni reali degli edifici OSM.</p>`;
        break;
      }
      case 'settings': {
        const st = s.settings;
        content.innerHTML = `<h2>Impostazioni</h2>
          <p><b>NAPOLI LIFE — OpenCode Edition</b></p>
          <p>Versione <b>${VERSION}</b> · schema salvataggi v${SAVE_VERSION} · build ${BUILD_ID}</p>
          <p class="tag">Standard: 1 m = 16 px · interni 48 px/m · scale 1</p>
          <button data-act="toggle:music">Musica: ${st.music ? 'ON' : 'OFF'}</button>
          <button data-act="toggle:ambience">Ambiente: ${st.ambience ? 'ON' : 'OFF'}</button>
          <button data-act="toggle:fps">FPS: ${st.showFps ? 'ON' : 'OFF'}</button>
          <button data-act="volume">Volume: ${Math.round(st.volume * 100)}%</button>
          <h3>Salvataggi</h3>
          <button data-act="save">Salva ora</button>
          <button data-act="export">Esporta</button>
          <button data-act="import">Importa</button>
          <button class="secondary" data-act="reset">Azzera partita</button>
          <h3>Comandi</h3><p>WASD/frecce · Shift corri · E interagisci · ↑/↓ in treno frena/accelera<br />Touch: joystick + CORRI + E. Ruota lo schermo: nessun reload.</p>
          <h3>Fonti</h3><p>© OpenStreetMap contributors (ODbL). Dati captured ${this.world?.meta.osm_captured_utc?.slice(0, 10) ?? 'n/d'}.</p>`;
        break;
      }
    }
    content.querySelectorAll<HTMLButtonElement>('button[data-act]').forEach(btn => {
      btn.addEventListener('click', () => this.handleAction(btn.dataset.act!));
    });
  }

  private minuteLabel(m: number): string {
    return `${String(Math.floor(m / 60) % 24).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;
  }

  private itemName(key: string): string {
    const names: Record<string, string> = {
      caffe: 'Espresso', biglietto: 'Biglietto EAV', pacco: 'Pacco',
      chiavi: 'Chiavi', dolce: 'Dolce', ticket: 'Biglietto EAV',
      bevanda: 'Bevanda', pizza: 'Pizza al taglio', acqua: 'Acqua',
      bookshelf: 'Libreria', plant: 'Pianta',
    };
    return names[key] ?? MENU[key]?.name ?? key;
  }

  private lookName(key: string): string {
    const names: Record<string, string> = {
      player: 'Azzurro', resident: 'Corallo', worker: 'Giallo', teen: 'Viola',
      elderly: 'Verde', railway: 'EAV', pizzaiolo: 'Pizzaiolo',
    };
    return names[key] ?? key;
  }

  private handleAction(act: string): void {
    const scene: any = this.scene;
    if (act.startsWith('look:')) {
      scene.setAppearance?.(act.split(':')[1]);
      this.toast('Aspetto aggiornato');
      this.panelOpen = ''; this.openPanel('profile'); return;
    } else if (act.startsWith('eat:')) {
      scene.consumeItem?.(act.split(':')[1]);
      this.panelOpen = ''; this.openPanel('inventory'); return;
    } else if (act.startsWith('toggle:')) {
      const key = act.split(':')[1];
      const map: Record<string, string> = { music: 'music', ambience: 'ambience', fps: 'showFps' };
      scene.save.settings[map[key]] = !scene.save.settings[map[key]];
      scene.applyAudioSettings?.();
    } else if (act === 'volume') {
      scene.save.settings.volume = scene.save.settings.volume >= 1 ? 0.2 : scene.save.settings.volume + 0.2;
      scene.applyAudioSettings?.();
    } else if (act.startsWith('vehicle:')) {
      const parts = act.split(':');
      const kind = parts[2] as VehicleKind;
      if (parts[1] === 'buy') scene.buyVehicle?.(kind);
      else if (parts[1] === 'mount') scene.mountVehicle?.(kind);
      else if (parts[1] === 'dismount') scene.dismountVehicle?.();
      else if (parts[1] === 'refuel') scene.refuelVehicle?.();
      this.panelOpen = ''; this.openPanel('vehicles'); return;
    } else if (act.startsWith('gift:')) {
      const [, id, item] = act.split(':');
      scene.giftNPC?.(id, item);
      this.panelOpen = ''; this.openPanel('relations'); return;
    } else if (act === 'home:second') {
      scene.buySecondHome?.();
      this.panelOpen = ''; this.openPanel('wallet'); return;
    } else if (act === 'save') {
      scene.manualSave?.(); this.toast('Partita salvata');
    } else if (act === 'export') {
      const blob = new Blob([scene.exportSave?.() ?? ''], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `napoli-life-save-v${SAVE_VERSION}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
      this.toast('Salvataggio esportato');
    } else if (act === 'import') {
      const text = window.prompt('Incolla qui il JSON del salvataggio:');
      if (text && scene.importSave?.(text)) this.toast('Salvataggio importato');
      else if (text) this.toast('File non valido');
    } else if (act === 'reset') {
      if (window.confirm('Azzzerare la partita? Il salvataggio attuale verrà rimosso.')) {
        scene.resetSave?.(); this.toast('Partita azzerata');
      }
    }
    this.panelOpen = '';
    this.openPanel('settings');
  }

  private renderMap(): void {
    const canvas = document.getElementById('minimap') as HTMLCanvasElement | null;
    if (!canvas || !this.world) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const size = canvas.width;
    const bounds = this.world.meta.play_bounds ?? [WORLD_BOUNDS.minX, WORLD_BOUNDS.minY, WORLD_BOUNDS.maxX, WORLD_BOUNDS.maxY];
    const [minX, minY, maxX, maxY] = bounds;
    const width = maxX - minX, height = maxY - minY;
    const scale = Math.min(size / width, size / height);
    const ox = (size - width * scale) / 2, oy = (size - height * scale) / 2;
    const tx = (x: number) => ox + (x - minX) * scale;
    const ty = (y: number) => oy + (y - minY) * scale;
    const path = (pts: [number, number][]) => {
      ctx.beginPath();
      pts.forEach((p, i) => i ? ctx.lineTo(tx(p[0]), ty(p[1])) : ctx.moveTo(tx(p[0]), ty(p[1])));
    };
    ctx.fillStyle = '#c8bfab';
    ctx.fillRect(0, 0, size, size);
    for (const lc of this.world.landcover) {
      if (lc.footprint.length < 3) continue;
      ctx.fillStyle = '#7c995f';
      path(lc.footprint); ctx.closePath(); ctx.fill();
    }
    for (const r of this.world.roads) {
      ctx.strokeStyle = r.kind.includes('way') || r.kind === 'steps' ? '#e6ddc9' : '#646663';
      ctx.lineWidth = Math.max(1, r.width_m * scale * 0.6);
      path(r.points); ctx.stroke();
    }
    for (const rail of this.world.rails) {
      ctx.strokeStyle = '#353535'; ctx.lineWidth = 2;
      path(rail.points); ctx.stroke();
    }
    ctx.fillStyle = '#a8917f';
    for (const b of this.world.buildings) {
      path(b.footprint); ctx.closePath(); ctx.fill();
    }
    ctx.fillStyle = '#e2b83c';
    ctx.fillRect(tx(0) - 3, ty(0) - 3, 6, 6);
    // La Pizzeria Carpe Diem rimane un riferimento verificato della v0.5.
    ctx.fillStyle = '#b4472f';
    ctx.fillRect(tx(-126.3) - 3, ty(117.9) - 3, 6, 6);
    for (const poi of [...(this.world.fictional_pois ?? []), ...this.world.pois]) {
      if (!/conad|coop|tabacch|bookmaker|scommesse|panificio|forno/i.test(poi.name)) continue;
      ctx.fillStyle = poi.fictional ? '#e2b83c' : '#1f4e79';
      ctx.fillRect(tx(poi.x) - 2, ty(poi.y) - 2, 4, 4);
    }
    const player: any = (this.scene as any).player;
    if (player) {
      ctx.fillStyle = '#1f4e79';
      ctx.beginPath();
      ctx.arc(tx(player.mx), ty(player.my), 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = 'white'; ctx.lineWidth = 1; ctx.stroke();
    }
  }
}
