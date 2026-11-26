import Phaser from 'phaser';
import { SECTOR_M, SPAWN } from '../config';
import { tileOrigins, WorldLoader } from '../world/WorldLoader';

/** Avvio: scarica i dati già elaborati (nessuna API esterna) e carica solo il necessario. */
export class BootScene extends Phaser.Scene {
  constructor() { super('Boot'); }

  create(): void {
    const label = this.add.text(this.scale.width / 2, this.scale.height / 2,
      'Caricamento di Pianura…', { fontFamily: 'monospace', fontSize: '16px', color: '#f4ebd6' })
      .setOrigin(0.5);
    this.cameras.main.setBackgroundColor('#20262c');

    WorldLoader.load().then(({ world, buildings, interiors, tiles, sprites, audio }) => {
      const base = import.meta.env.BASE_URL;

      // Solo i settori visibili all'avvio: il resto viene caricato da SectorStreamer.
      const sx = Math.floor(SPAWN.x / SECTOR_M) * SECTOR_M;
      const sy = Math.floor(SPAWN.y / SECTOR_M) * SECTOR_M;
      const origins = new Set(tileOrigins(tiles).map(([x, y]) => `${x}:${y}`));
      for (let dx = -1; dx <= 1; dx++) {
        for (let dy = -1; dy <= 1; dy++) {
          const x = sx + dx * SECTOR_M, y = sy + dy * SECTOR_M;
          if (!origins.has(`${x}:${y}`)) continue;
          this.load.image(`sector_${x}_${y}`, `${base}assets/tiles/sector_${x}_${y}.png`);
        }
      }
      // Edifici unici costruiti dai perimetri OSM.
      for (const b of buildings) {
        this.load.image(`bld_${b.id.replace('/', '_')}`, `${base}${b.sprite}`);
      }
      // Personaggi (sheet 4 direzioni x 4 frame) e oggetti, dal manifest versionato.
      const chars: string[] = [];
      const entries = Object.values(sprites.sprites ?? {});
      for (const entry of entries) {
        const file = entry.file ?? `${entry.name}.png`;
        if (entry.type === 'character') {
          chars.push(entry.name);
          this.load.spritesheet(entry.name, `${base}assets/sprites/${file}`, { frameWidth: 16, frameHeight: 32 });
        } else {
          this.load.image(entry.name, `${base}assets/sprites/${file}`);
        }
      }
      // Interni presenti nel manifest (5 storici + 6 nuovi della 0.6).
      for (const name of Object.keys(interiors)) {
        this.load.image(`room_${name}`, `${base}assets/interiors/${name}.png`);
      }
      for (const file of audio.files ?? []) {
        this.load.audio(file.replace(/\.wav$/, ''), `${base}assets/audio/${file}`);
      }

      this.load.on('progress', (p: number) => { label.setText(`Caricamento di Pianura… ${Math.round(p * 100)}%`); });
      this.load.once('complete', () => {
        const dirs = ['down', 'left', 'right', 'up'];
        for (const name of chars) {
          dirs.forEach((dir, row) => {
            const key = `${name}_${dir}`;
            if (!this.anims.exists(key)) {
              this.anims.create({
                key,
                frames: this.anims.generateFrameNumbers(name, { start: row * 4, end: row * 4 + 3 }),
                frameRate: 7, repeat: -1,
              });
            }
          });
        }
        this.registry.set('gameData', { world, buildings, interiors, tiles });
        this.scene.start('World');
      });
      this.load.start();
    }).catch((err) => {
      label.setText('Errore caricamento dati: ' + err.message);
      console.error('[Boot]', err);
    });
  }
}
