import Phaser from 'phaser';
import { NPC_SPEED, PPM, PLAYER_SPEED, RUN_SPEED } from '../config';
import { CollisionWorld } from '../world/Collision';

/** Protagonista: 8 direzioni, camminata/corsa, piedi come punto di ancoraggio profondità. */
export class Player {
  sprite: Phaser.GameObjects.Sprite;
  mx: number;
  my: number;
  appearance: string;
  private direction = 0; // 0 giù, 1 sinistra, 2 destra, 3 su
  private steps = 0;

  constructor(private scene: Phaser.Scene, x: number, y: number, appearance: string,
              private collision: CollisionWorld, private onStep: () => void) {
    this.mx = x;
    this.my = y;
    this.appearance = appearance;
    this.sprite = scene.add.sprite(x * PPM, y * PPM, appearance, 0);
    // Sprite 16x32: i piedi sono a y=30 (0,9375 dell'altezza).
    this.sprite.setOrigin(0.5, 30 / 32);
    this.sprite.setDepth(y * PPM + 1);
  }

  setAppearance(key: string): void {
    this.appearance = key;
    this.sprite.setTexture(key);
  }

  update(deltaSec: number, vx: number, vy: number, running: boolean): void {
    const moving = Math.abs(vx) > 0.05 || Math.abs(vy) > 0.05;
    if (moving) {
      const speed = running ? RUN_SPEED : PLAYER_SPEED;
      const pos = this.collision.resolve(this.mx, this.my, vx * speed * deltaSec, vy * speed * deltaSec, 0.26);
      this.mx = pos.x;
      this.my = pos.y;
      if (Math.abs(vx) > Math.abs(vy)) this.direction = vx > 0 ? 2 : 1;
      else this.direction = vy > 0 ? 0 : 3;
      this.steps += deltaSec * (running ? 3.4 : 2.1);
      if (this.steps >= 1) { this.steps = 0; this.onStep(); }
      const frame = 1 + (Math.floor(this.steps * 4) % 3);
      this.sprite.setFrame(this.direction * 4 + frame);
    } else {
      this.sprite.setFrame(this.direction * 4);
    }
    this.sprite.setPosition(this.mx * PPM, this.my * PPM);
    this.sprite.setDepth(this.my * PPM + 1);
  }
}
