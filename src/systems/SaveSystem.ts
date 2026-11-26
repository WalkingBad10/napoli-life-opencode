import { SAVE_KEY, SAVE_VERSION, SPAWN } from '../config';
import type { SaveData } from '../types';

const baseSave = (): SaveData => ({
  version: SAVE_VERSION,
  savedAt: new Date().toISOString(),
  player: { x: SPAWN.x, y: SPAWN.y, appearance: 'player' },
  time: { minute: 7 * 60, day: 1 },
  money: 35,
  inventory: {},
  quests: [],
  flags: {},
  settings: { music: true, ambience: true, volume: 0.7, showFps: false },
  stats: { steps: 0, coffees: 0, tickets: 0, jobs: 0 },
});

/** Migrazioni cumulative: i salvataggi vecchi restano giocabili dopo gli aggiornamenti. */
function migrate(raw: any): SaveData {
  const fresh = baseSave();
  if (!raw || typeof raw !== 'object') return fresh;
  let v = Number(raw.version) || 1;
  const data: any = { ...raw };

  if (v < 2) {
    // v1 -> v2: moneta da intero a euro decimali, inventariointrodotto
    if (typeof data.money === 'number' && data.money > 1000) data.money = data.money / 100;
    data.inventory = data.inventory ?? {};
    v = 2;
  }
  if (v < 3) {
    // v2 -> v3: impostazioni audio e statistiche
    data.settings = { ...fresh.settings, ...(data.settings ?? {}) };
    data.stats = { ...fresh.stats, ...(data.stats ?? {}) };
    data.flags = data.flags ?? {};
    v = 3;
  }

  return {
    ...fresh,
    ...data,
    version: SAVE_VERSION,
    player: { ...fresh.player, ...(data.player ?? {}) },
    time: { ...fresh.time, ...(data.time ?? {}) },
    inventory: { ...fresh.inventory, ...(data.inventory ?? {}) },
    settings: { ...fresh.settings, ...(data.settings ?? {}) },
    stats: { ...fresh.stats, ...(data.stats ?? {}) },
    flags: { ...fresh.flags, ...(data.flags ?? {}) },
    quests: Array.isArray(data.quests) ? data.quests : [],
  };
}

export class SaveSystem {
  static load(): SaveData {
    try {
      const text = localStorage.getItem(SAVE_KEY);
      if (!text) return baseSave();
      return migrate(JSON.parse(text));
    } catch (e) {
      console.warn('[SaveSystem] ripristino salvataggio predefinito', e);
      return baseSave();
    }
  }

  static save(data: SaveData): boolean {
    try {
      data.version = SAVE_VERSION;
      data.savedAt = new Date().toISOString();
      localStorage.setItem(SAVE_KEY, JSON.stringify(data));
      return true;
    } catch (e) {
      console.error('[SaveSystem] salvataggio fallito', e);
      return false;
    }
  }

  static export(data: SaveData): string {
    return JSON.stringify(data, null, 2);
  }

  static import(text: string): SaveData | null {
    try {
      const parsed = migrate(JSON.parse(text));
      SaveSystem.save(parsed);
      return parsed;
    } catch (e) {
      console.error('[SaveSystem] import non valido', e);
      return null;
    }
  }

  static reset(): SaveData {
    localStorage.removeItem(SAVE_KEY);
    return baseSave();
  }
}
