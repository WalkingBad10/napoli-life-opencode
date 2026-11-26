import Phaser from 'phaser';
import type { SaveData } from '../types';

/** Audio originale sintetizzato: loop ambientali, colonna sonora ed effetti. */
export class AudioSystem {
  private sounds: Record<string, any> = {};
  private started = false;

  constructor(private scene: Phaser.Scene) {
    window.addEventListener('napoli-start', () => this.start());
    if ((window as any).__napoliStarted) this.start();
  }

  start(): void {
    if (this.started) return;
    this.started = true;
    const manager = this.scene.sound as any;
    const cache = this.scene.cache.audio as any;
    const mk = (key: string, loop: boolean, volume: number) => {
      if (!cache.exists(key)) return;
      try {
        const s = manager.add(key, { loop, volume });
        this.sounds[key] = s;
        if (loop) s.play();
      } catch (e) { console.warn('[audio] loop non disponibile', key, e); }
    };
    mk('ambience', true, 0.24);
    mk('music', true, 0.16);
    this.apply(this.lastSettings ?? { music: true, ambience: true, volume: 0.7, showFps: false });
  }

  private lastSettings: SaveData['settings'] | null = null;

  apply(settings: SaveData['settings']): void {
    this.lastSettings = settings;
    const v = settings.volume;
    for (const [name, key] of [['ambience', 'ambience'], ['music', 'music']] as const) {
      const s = this.sounds[key];
      if (!s) continue;
      try {
        s.setMute(!settings[name]);
        s.setVolume((name === 'music' ? 0.16 : 0.24) * v);
      } catch (e) { console.warn('[audio] impostazioni non applicate', key, e); }
    }
  }

  sfx(key: 'step' | 'coin' | 'door' | 'train', volume = 0.25): void {
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
}
