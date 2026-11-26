import Phaser from 'phaser';
import type { DayPhase } from './TimeSystem';
import type { SaveData } from '../types';

type SfxKey = 'step' | 'coin' | 'door' | 'train' | 'cash' | 'eat' | 'sleep' | 'ui'
  | 'engine' | 'scooter' | 'shop_bell' | 'relationship' | 'traffic' | 'market';

const LOOPS: Record<string, number> = {
  ambience: 0.20,
  music: 0.13,
  birds: 0.12,
  night: 0.14,
  crowd: 0.12,
  bar_murmur: 0.11,
  traffic: 0.09,
  market: 0.10,
};

/** Audio originale sintetizzato: loop ambientali a zone, colonna sonora ed effetti. */
export class AudioSystem {
  private sounds: Record<string, any> = {};
  private started = false;
  private lastSettings: SaveData['settings'] | null = null;
  private loopVolumes: Record<string, number> = {};
  private lastSfx = '';
  private sfxCount = 0;
  private zone = '';

  constructor(private scene: Phaser.Scene) {
    window.addEventListener('napoli-start', () => this.start());
    if ((window as any).__napoliStarted) this.start();
  }

  start(): void {
    if (this.started) return;
    this.started = true;
    const manager = this.scene.sound as any;
    const cache = this.scene.cache.audio as any;
    for (const [key, volume] of Object.entries(LOOPS)) {
      if (!cache.exists(key)) continue;
      try {
        const s = manager.add(key, { loop: true, volume });
        this.sounds[key] = s;
        this.loopVolumes[key] = volume;
        s.play();
      } catch (e) { console.warn('[audio] loop non disponibile', key, e); }
    }
    this.apply(this.lastSettings ?? { music: true, ambience: true, volume: 0.7, showFps: false });
  }

  apply(settings: SaveData['settings']): void {
    this.lastSettings = settings;
    this.applyZone();
  }

  /** Chiamato a ogni cambio di fase o ingresso in un interno: al massimo tre loop attivi. */
  setZone(phase: DayPhase, room: string | null, population: number): void {
    const zone = `${room ?? 'world'}:${phase}:${population > 0.65 ? 'busy' : 'quiet'}`;
    if (zone === this.zone) return;
    this.zone = zone;
    this.applyZone(phase, room, population);
  }

  private applyZone(phase?: DayPhase, room?: string | null, population?: number): void {
    const s = this.lastSettings;
    if (!s) return;
    const v = s.volume;
    const p = this.zone.split(':');
    const place = room !== undefined ? room : p[0] ?? 'world';
    const time = phase ?? (p[1] as DayPhase | undefined) ?? 'day';
    const busy = population !== undefined ? population > 0.65 : p[2] === 'busy';
    const wanted: Record<string, number> = {
      ambience: place === 'world' && time === 'day' ? 1 : 0.35,
      music: place === 'world' ? 0.55 : 0.3,
      birds: place === 'world' && (time === 'dawn' || time === 'day') ? 1 : 0,
      night: time === 'night' || time === 'dusk' ? 0.9 : 0,
      crowd: place === 'world' && busy && time !== 'night' ? 0.85 : 0,
      bar_murmur: place === 'bar' || place === 'pizzeria' ? 1 : 0,
      traffic: place === 'world' && busy && time !== 'night' ? 0.5 : 0.12,
      market: place === 'supermarket' || place === 'bakery' || place === 'clothing' ? 1 : 0,
    };
    for (const [key, sound] of Object.entries(this.sounds)) {
      try {
        const enabled = key === 'music' ? s.music : s.ambience;
        const factor = wanted[key] ?? 1;
        sound.setMute(!enabled || factor <= 0);
        sound.setVolume((this.loopVolumes[key] ?? LOOPS[key] ?? 0.15) * v * factor);
      } catch (e) { console.warn('[audio] impostazioni non applicate', key, e); }
    }
  }

  sfx(key: SfxKey, volume = 0.25): void {
    this.lastSfx = key;
    this.sfxCount++;
    try {
      const manager = this.scene.sound as any;
      const cache = this.scene.cache.audio as any;
      if (!this.sounds[key] && cache.exists(key)) {
        this.sounds[key] = manager.add(key, { volume });
      }
      const s = this.sounds[key];
      if (s && !s.isPlaying) s.play();
    } catch (e) { console.warn('[audio] effetto non disponibile', key, e); }
  }

  /** Stato di sola lettura per i test automatici. */
  state(): { started: boolean; loops: string[]; lastSfx: string; sfxCount: number; zone: string } {
    return {
      started: this.started,
      loops: Object.keys(LOOPS).filter(k => !!this.sounds[k]),
      lastSfx: this.lastSfx,
      sfxCount: this.sfxCount,
      zone: this.zone,
    };
  }
}
