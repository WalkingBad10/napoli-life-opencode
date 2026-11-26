import Phaser from 'phaser';
import type { Point } from '../types';

type KeyMap = Record<string, Phaser.Input.Keyboard.Key>;

/** Tastiera, joystick touch, pulsanti virtuali e gamepad in un'unica interfaccia. */
export class InputSystem {
  private keys: KeyMap;
  private interactPending = false;
  private cancelPending = false;
  touchVector: Point = { x: 0, y: 0 };
  touchRun = false;
  enabled = true;

  constructor(private scene: Phaser.Scene) {
    const kb = scene.input.keyboard;
    this.keys = (kb?.addKeys('W,A,S,D,UP,DOWN,LEFT,RIGHT,SHIFT,E,ESC') ?? {}) as KeyMap;
    kb?.on('keydown-E', () => { this.interactPending = true; });
    kb?.on('keydown-SPACE', () => { this.interactPending = true; });
    kb?.on('keydown-ESC', () => { this.cancelPending = true; });
    window.addEventListener('napoli-interact', () => { this.interactPending = true; });
  }

  private pad(): any { return this.scene.input.gamepad?.getPad(0) ?? null; }
  private pressed(pad: any, index: number): boolean { return !!pad?.buttons?.[index]?.pressed; }

  getVector(): Point {
    if (!this.enabled) return { x: 0, y: 0 };
    let x = 0, y = 0;
    const k = this.keys;
    if (k.A?.isDown || k.LEFT?.isDown) x -= 1;
    if (k.D?.isDown || k.RIGHT?.isDown) x += 1;
    if (k.W?.isDown || k.UP?.isDown) y -= 1;
    if (k.S?.isDown || k.DOWN?.isDown) y += 1;

    const pad = this.pad();
    if (pad) {
      x += Number(pad.axes?.[0]?.getValue?.() ?? 0);
      y += Number(pad.axes?.[1]?.getValue?.() ?? 0);
      if (this.pressed(pad, 14)) x -= 1;
      if (this.pressed(pad, 15)) x += 1;
      if (this.pressed(pad, 12)) y -= 1;
      if (this.pressed(pad, 13)) y += 1;
    }
    if (Math.abs(this.touchVector.x) > 0.15) x += this.touchVector.x;
    if (Math.abs(this.touchVector.y) > 0.15) y += this.touchVector.y;

    const len = Math.hypot(x, y);
    if (len > 1) { x /= len; y /= len; }
    return { x, y };
  }

  isRunning(): boolean {
    return !!(this.keys.SHIFT?.isDown || this.touchRun ||
      this.pressed(this.pad(), 0) || this.pressed(this.pad(), 5));
  }

  consumeInteract(): boolean {
    const pending = this.interactPending || this.pressed(this.pad(), 1);
    this.interactPending = false;
    return pending && this.enabled;
  }

  consumeCancel(): boolean {
    const v = this.cancelPending || !!this.keys.ESC?.isDown;
    this.cancelPending = false;
    return v;
  }

  setTouch(x: number, y: number): void {
    this.touchVector.x = x;
    this.touchVector.y = y;
  }

  /** Evita che un E premuto durante un dialogo scateni un'interazione alla chiusura. */
  clearPending(): void {
    this.interactPending = false;
    this.cancelPending = false;
  }
}
