import Phaser from 'phaser';
import { WorldLoader } from '../world/WorldLoader';

/** Avvio: scarica i dati già elaborati (nessuna API esterna) e carica tutti gli asset. */
export class BootScene extends Phaser.Scene {
  constructor() { super('Boot'); }

  create(): void {
    const label = this.add.text(this.scale.width / 2, this.scale.height / 2,
      'Caricamento di Pianura…', { fontFamily: 'monospace', fontSize: '16px', color: '#f4ebd6' })
      .setOrigin(0.5);
    this.cameras.main.setBackgroundColor('#20262c');

    WorldLoader.load().then(({ world, buildings, interiors }) => {
      const base = import.meta.env.BASE_URL;

      // Settori del suolo (separati, pronti per il culling in WorldScene)
      for (const x of [-192, -128, -64, 0, 64, 128]) {
        for (const y of [-192, -128, -64, 0, 64, 128]) {
          const key = `sector_${x}_${y}`;
          this.load.image(key, `${base}assets/tiles/${key}.png`);
        }
      }
      // Edifici unici costruiti dai perimetri OSM
      for (const b of buildings) {
        this.load.image(`bld_${b.id.replace('/', '_')}`, `${base}${b.sprite}`);
      }
      // Personaggi (sheet 4 direzioni x 4 frame)
      const chars = ['player', 'resident', 'worker', 'elderly', 'teen', 'railway', 'vendor'];
      for (const name of chars) {
        this.load.spritesheet(name, `${base}assets/sprites/${name}.png`,
          { frameWidth: 16, frameHeight: 32 });
      }
      // Oggetti, interni, treno e audio
      for (const name of ['lamp', 'bin', 'scooter', 'car_red', 'car_silver', 'bus', 'tree',
                          'planter', 'bench', 'sign', 'traffic_light', 'ticket_machine',
                          'dog', 'cat', 'parcel', 'keys', 'coffee', 'ticket', 'train_eav']) {
        this.load.image(name, `${base}assets/sprites/${name}.png`);
      }
      for (const name of ['station', 'bar', 'shop', 'home']) {
        this.load.image(`room_${name}`, `${base}assets/interiors/${name}.png`);
      }
      for (const name of ['ambience', 'music', 'step', 'coin', 'door', 'train']) {
        this.load.audio(name, `${base}assets/audio/${name}.wav`);
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
        this.registry.set('gameData', { world, buildings, interiors });
        this.scene.start('World');
      });
      this.load.start();
    }).catch((err) => {
      label.setText('Errore caricamento dati: ' + err.message);
      console.error('[Boot]', err);
    });
  }
}
