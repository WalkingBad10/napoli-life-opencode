import Phaser from 'phaser';
import { BUILD_ID, SAVE_VERSION, VERSION } from '../config';
import { QUEST_DEFS } from '../systems/QuestSystem';
import type { WorldData } from '../types';

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

  setHUD(clock: string, money: number): void {
    $('hud-clock').textContent = clock;
    $('hud-money').textContent = `€ ${money.toFixed(2).replace('.', ',')}`;
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
    (this.scene as any).inputSystem && ((this.scene as any).inputSystem.enabled = true);
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
        content.innerHTML = '<h2>Mappa di Pianura</h2><canvas id="minimap" width="320" height="320"></canvas><p class="tag">Dati OSM reali · 300 × 300 m</p><p>La stazione è indicata in giallo, tu in blu.</p>';
        this.renderMap();
        break;
      }
      case 'inventory': {
        const entries = Object.entries(s.inventory as Record<string, number>);
        content.innerHTML = `<h2>Inventario</h2>${entries.length ? entries.map(([k, v]) => `<span class="tag">${this.itemName(k)} × ${v}</span>`).join('') : '<p>Zaino vuoto. Il quartiere ti aspetta.</p>'}`;
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
        const clock = (this.scene as any).clock?.clock ?? '--:--';
        content.innerHTML = `<h2>Telefono</h2><p><b>${clock}</b> · Giorno ${(this.scene as any).clock?.day ?? 1}</p><p>📞 EAV Circumflegrea: 800 001 788</p><p>📞 Bar Pianura: 081 000 0000</p><p class="tag">Nessun account richiesto</p>`;
        break;
      }
      case 'wallet': {
        content.innerHTML = `<h2>Portafoglio</h2><p><b>€ ${Number(s.money).toFixed(2).replace('.', ',')}</b></p><p>Hai comprato: ${Object.entries(s.inventory).filter(([k]) => k !== 'parcel' && k !== 'keys').map(([k]) => this.itemName(k)).join(', ') || 'nulla'}</p><button data-act="export">Esporta salvataggio</button><button data-act="import">Importa salvataggio</button>`;
        break;
      }
      case 'profile': {
        const looks = ['player', 'resident', 'worker', 'teen', 'elderly', 'railway'];
        content.innerHTML = `<h2>Profilo</h2><p>Aspetto del protagonista</p>${looks.map(l => `<button data-act="look:${l}">${l === 'player' ? 'Azzurro' : l === 'resident' ? 'Corallo' : l === 'worker' ? 'Giallo' : l === 'teen' ? 'Viola' : l === 'elderly' ? 'Verde' : 'EAV'}</button>`).join('')}<p class="tag">Passi: ${s.stats.steps} · Caffè: ${s.stats.coffees} · Biglietti: ${s.stats.tickets}</p>`;
        break;
      }
      case 'settings': {
        const st = s.settings;
        content.innerHTML = `<h2>Impostazioni</h2>
          <p><b>NAPOLI LIFE — OpenCode Edition</b></p>
          <p>Versione <b>${VERSION}</b> · schema salvataggi v${SAVE_VERSION} · build ${BUILD_ID}</p>
          <button data-act="toggle:music">Musica: ${st.music ? 'ON' : 'OFF'}</button>
          <button data-act="toggle:ambience">Ambiente: ${st.ambience ? 'ON' : 'OFF'}</button>
          <button data-act="toggle:fps">FPS: ${st.showFps ? 'ON' : 'OFF'}</button>
          <button data-act="volume">Volume: ${Math.round(st.volume * 100)}%</button>
          <h3>Salvataggi</h3>
          <button data-act="save">Salva ora</button>
          <button data-act="export">Esporta</button>
          <button data-act="import">Importa</button>
          <button class="secondary" data-act="reset">Azzera partita</button>
          <h3>Comandi</h3><p>WASD/frecce · Shift corri · E interagisci<br />Touch: joystick + CORRI + E. Ruota lo schermo: nessun reload.</p>
          <h3>Fonti</h3><p>© OpenStreetMap contributors (ODbL). Dati captured ${this.world?.meta.osm_captured_utc?.slice(0, 10) ?? 'n/d'}.</p>`;
        break;
      }
    }
    content.querySelectorAll<HTMLButtonElement>('button[data-act]').forEach(btn => {
      btn.addEventListener('click', () => this.handleAction(btn.dataset.act!));
    });
  }

  private itemName(key: string): string {
    const names: Record<string, string> = {
      caffe: 'Espresso', biglietto: 'Biglietto EAV', pacco: 'Pacco',
      chiavi: 'Chiavi', dolce: 'Dolce', ticket: 'Biglietto EAV',
    };
    return names[key] ?? key;
  }

  private handleAction(act: string): void {
    const scene: any = this.scene;
    if (act.startsWith('look:')) {
      scene.setAppearance?.(act.split(':')[1]);
      this.toast('Aspetto aggiornato');
    } else if (act.startsWith('toggle:')) {
      const key = act.split(':')[1];
      const map: Record<string, string> = { music: 'music', ambience: 'ambience', fps: 'showFps' };
      scene.save.settings[map[key]] = !scene.save.settings[map[key]];
      scene.applyAudioSettings?.();
    } else if (act === 'volume') {
      scene.save.settings.volume = scene.save.settings.volume >= 1 ? 0.2 : scene.save.settings.volume + 0.2;
      scene.applyAudioSettings?.();
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
    this.openPanel(act.startsWith('look:') ? 'profile' : 'settings');
  }

  private renderMap(): void {
    const canvas = document.getElementById('minimap') as HTMLCanvasElement | null;
    if (!canvas || !this.world) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const size = canvas.width;
    const scale = size / 300; // 300 x 300 metri
    const tx = (m: number) => (m + 150) * scale;
    ctx.fillStyle = '#c8bfab';
    ctx.fillRect(0, 0, size, size);
    for (const lc of this.world.landcover) {
      if (lc.footprint.length < 3) continue;
      ctx.fillStyle = '#7c995f';
      ctx.beginPath();
      lc.footprint.forEach((p, i) => i ? ctx.lineTo(tx(p[0]), tx(p[1])) : ctx.moveTo(tx(p[0]), tx(p[1])));
      ctx.closePath(); ctx.fill();
    }
    for (const r of this.world.roads) {
      ctx.strokeStyle = r.kind.includes('way') || r.kind === 'steps' ? '#e6ddc9' : '#646663';
      ctx.lineWidth = Math.max(1, r.width_m * scale * 0.6);
      ctx.beginPath();
      r.points.forEach((p, i) => i ? ctx.lineTo(tx(p[0]), tx(p[1])) : ctx.moveTo(tx(p[0]), tx(p[1])));
      ctx.stroke();
    }
    for (const rail of this.world.rails) {
      ctx.strokeStyle = '#353535'; ctx.lineWidth = 2;
      ctx.beginPath();
      rail.points.forEach((p, i) => i ? ctx.lineTo(tx(p[0]), tx(p[1])) : ctx.moveTo(tx(p[0]), tx(p[1])));
      ctx.stroke();
    }
    ctx.fillStyle = '#a8917f';
    for (const b of this.world.buildings) {
      ctx.beginPath();
      b.footprint.forEach((p, i) => i ? ctx.lineTo(tx(p[0]), tx(p[1])) : ctx.moveTo(tx(p[0]), tx(p[1])));
      ctx.closePath(); ctx.fill();
    }
    ctx.fillStyle = '#e2b83c';
    ctx.fillRect(tx(0) - 3, tx(0) - 3, 6, 6);
    const player: any = (this.scene as any).player;
    if (player) {
      ctx.fillStyle = '#1f4e79';
      ctx.beginPath();
      ctx.arc(tx(player.mx), tx(player.my), 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = 'white'; ctx.lineWidth = 1; ctx.stroke();
    }
  }
}
