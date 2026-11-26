import Phaser from 'phaser';
import { NPC_SPEED, PPM } from '../config';
import type { Point } from '../types';
import { CollisionWorld } from '../world/Collision';

export interface NPCDialogue {
  morning: string[];
  afternoon: string[];
  evening: string[];
}

/** Residente con routine giornaliera, percorso pedonale e dialoghi variabili. */
export class NPC {
  sprite: Phaser.GameObjects.Sprite;
  mx: number;
  my: number;
  private target = 0;
  private pause = 0;
  private facing = 0;
  private walkTime = 0;

  constructor(
    scene: Phaser.Scene,
    public readonly id: string,
    public readonly name: string,
    texture: string,
    x: number, y: number,
    private path: Point[],
    private dialogue: NPCDialogue,
    private collision: CollisionWorld,
  ) {
    this.mx = x; this.my = y;
    this.sprite = scene.add.sprite(x * PPM, y * PPM, texture, 0);
    this.sprite.setOrigin(0.5, 0.94);
    this.sprite.setDepth(y * PPM);
  }

  update(deltaSec: number, playerX: number, playerY: number, active: boolean, hour: number): void {
    const dist = Math.hypot(this.mx - playerX, this.my - playerY);
    this.sprite.setVisible(dist < 105);
    if (!active || !this.sprite.visible) return;

    if (this.pause > 0) {
      this.pause -= deltaSec;
      this.sprite.setFrame(this.facing * 4);
      return;
    }
    if (this.path.length < 2) return;
    const target = this.path[this.target];
    const dx = target.x - this.mx;
    const dy = target.y - this.my;
    const len = Math.hypot(dx, dy);
    if (len < 0.8) {
      this.target = (this.target + 1) % this.path.length;
      this.pause = 1.5 + Math.random() * 3.5;
      return;
    }
    const ux = dx / len, uy = dy / len;
    const pos = this.collision.resolve(this.mx, this.my, ux * NPC_SPEED * deltaSec, uy * NPC_SPEED * deltaSec, 0.3);
    this.mx = pos.x; this.my = pos.y;
    if (Math.abs(ux) > Math.abs(uy)) this.facing = ux > 0 ? 2 : 1;
    else this.facing = uy > 0 ? 0 : 3;
    this.walkTime += deltaSec * 2.4;
    this.sprite.setFrame(this.facing * 4 + (Math.floor(this.walkTime) % 3) + 1);
    this.sprite.setPosition(this.mx * PPM, this.my * PPM);
    this.sprite.setDepth(this.my * PPM);
  }

  talk(hour: number): string {
    const lines = hour < 12 ? this.dialogue.morning : hour < 18 ? this.dialogue.afternoon : this.dialogue.evening;
    return lines[Math.floor(Math.random() * lines.length)];
  }
}
