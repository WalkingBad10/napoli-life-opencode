import Phaser from 'phaser';
import { NPC_SPEED, PPM } from '../config';
import type { Point } from '../types';
import { CollisionWorld } from '../world/Collision';

export interface NPCDialogue {
  morning: string[];
  afternoon: string[];
  evening: string[];
}

export interface NPCAnchors {
  morning: Point;
  afternoon: Point;
  evening: Point;
  night: Point;
  /** Ore di attività: fuori da questo intervallo il residente resta nella zona notte. */
  activeFrom: number;
  activeTo: number;
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
  private anchor: Point | null = null;
  private routineCount = 0;
  private readonly seed: number;

  constructor(
    scene: Phaser.Scene,
    public readonly id: string,
    public readonly name: string,
    texture: string,
    x: number, y: number,
    private path: Point[],
    private dialogue: NPCDialogue,
    private collision: CollisionWorld,
    private anchors?: NPCAnchors,
  ) {
    this.mx = x; this.my = y;
    this.seed = [...id].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
    this.sprite = scene.add.sprite(x * PPM, y * PPM, texture, 0);
    this.sprite.setOrigin(0.5, 30 / 32);
    this.sprite.setDepth(y * PPM);
  }

  /** Chiamato a ogni cambio d'ora: cambia il punto di destinazione della routine. */
  applyHour(hour: number, minuteOfHour = 0): void {
    if (!this.anchors) return;
    const a = this.anchors;
    const working = hour >= a.activeFrom && hour < a.activeTo;
    const next = !working ? a.night : hour < 12 ? a.morning : hour < 18 ? a.afternoon : a.evening;
    const same = this.anchor && Math.abs(this.anchor.x - next.x) < 0.5 && Math.abs(this.anchor.y - next.y) < 0.5;
    this.anchor = next;
    if (!same) this.routineCount++;
    // Pause deterministiche: nessun Math.random nella simulazione.
    if (minuteOfHour === (this.seed % 12) * 5) this.pause = 1.2 + (this.seed % 7) * 0.3;
  }

  private destination(): Point | null {
    if (this.anchor) return this.anchor;
    return this.path[this.target] ?? null;
  }

  update(deltaSec: number, playerX: number, playerY: number, active: boolean, hour: number): void {
    const dist = Math.hypot(this.mx - playerX, this.my - playerY);
    this.sprite.setVisible(dist < 165);
    if (!active || !this.sprite.visible) return;

    if (this.pause > 0) {
      this.pause -= deltaSec;
      this.sprite.setFrame(this.facing * 4);
      return;
    }
    const target = this.destination();
    if (!target || Math.hypot(target.x - this.mx, target.y - this.my) < 0.6) {
      if (!this.anchor && this.path.length > 1) {
        this.target = (this.target + 1) % this.path.length;
        this.pause = 1.2 + ((this.seed + this.routineCount) % 8) * 0.35;
      } else if (this.anchor) {
        this.pause = 2 + ((this.seed + this.routineCount) % 6) * 0.4;
      }
      return;
    }
    const dx = target.x - this.mx;
    const dy = target.y - this.my;
    const len = Math.hypot(dx, dy);
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

  talk(hour: number, minute = 0): string {
    const lines = hour < 12 ? this.dialogue.morning : hour < 18 ? this.dialogue.afternoon : this.dialogue.evening;
    const index = (this.seed + hour * 7 + Math.floor(minute / 10)) % lines.length;
    return lines[index];
  }
}
