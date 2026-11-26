import Phaser from 'phaser';
import { PPM, WORLD_BOUNDS } from '../config';
import type { Point } from '../types';
import { CollisionWorld } from '../world/Collision';

export type VehicleKind = 'car_red' | 'car_silver' | 'car_blue' | 'motorcycle';

export interface VehicleSaveState {
  owned: VehicleKind[];
  active: VehicleKind | null;
  x: number;
  y: number;
  fuel: number;
}

export const VEHICLE_DEFS: Record<VehicleKind, {
  name: string; price: number; speed: number; fuelPerSecond: number; radius: number;
}> = {
  car_red: { name: 'Fiat 126', price: 850, speed: 7.5, fuelPerSecond: 0.035, radius: 0.9 },
  car_silver: { name: 'Auto compatta', price: 1200, speed: 9, fuelPerSecond: 0.045, radius: 1.0 },
  car_blue: { name: 'Utilitaria blu', price: 980, speed: 8, fuelPerSecond: 0.04, radius: 0.95 },
  motorcycle: { name: 'Vespa', price: 420, speed: 10.5, fuelPerSecond: 0.022, radius: 0.5 },
};

const FULL_TANK = 100;
const DISMOUNT_GAP = 0.4;

/** Veicoli acquistati e guidati dal giocatore: coordinate in metri, carburante 0..100. */
export class VehicleSystem {
  readonly sprite: Phaser.GameObjects.Sprite;
  private s: VehicleSaveState;

  constructor(scene: Phaser.Scene, state: VehicleSaveState, private collision: CollisionWorld) {
    this.s = state;
    const kind = state.active ?? 'car_red';
    this.sprite = scene.add.sprite(state.x * PPM, state.y * PPM, kind);
    this.applyOrigin(kind);
    this.syncSprite();
    this.sprite.setVisible(!!state.active);
  }

  get active(): VehicleKind | null { return this.s.active; }
  get fuel(): number { return this.s.fuel; }

  /** Il costo viene restituito al chiamante, che lo scala solo quando ok è true. */
  buy(kind: VehicleKind, money: number): { ok: boolean; cost: number; reason?: string } {
    const def = VEHICLE_DEFS[kind];
    if (!def) return { ok: false, cost: 0, reason: 'Veicolo sconosciuto' };
    if (this.s.owned.includes(kind)) return { ok: false, cost: 0, reason: 'Hai già questo veicolo' };
    if (money < def.price) return { ok: false, cost: 0, reason: 'Denaro insufficiente' };
    this.s.owned.push(kind);
    if (this.s.active === null) {
      this.s.active = kind;
      if (this.s.fuel <= 0) this.s.fuel = FULL_TANK;
      this.applyKind(kind);
    }
    return { ok: true, cost: def.price };
  }

  mount(kind: VehicleKind): boolean {
    if (!this.s.owned.includes(kind) || this.s.fuel <= 0) return false;
    this.s.active = kind;
    this.applyKind(kind);
    this.syncSprite();
    return true;
  }

  /** Scende sul lato libero del veicolo; il sprite resta a terra e nascosto. */
  dismount(): { x: number; y: number } | null {
    const kind = this.s.active;
    if (!kind) return null;
    const offset = VEHICLE_DEFS[kind].radius + DISMOUNT_GAP;
    const nx = -Math.sin(this.sprite.rotation);
    const ny = Math.cos(this.sprite.rotation);
    const a = clampToBounds(this.s.x + nx * offset, this.s.y + ny * offset);
    const b = clampToBounds(this.s.x - nx * offset, this.s.y - ny * offset);
    const spot = !this.collision.blocked(a.x, a.y, 0.26) ? a
      : (!this.collision.blocked(b.x, b.y, 0.26) ? b : clampToBounds(this.s.x, this.s.y));
    this.s.active = null;
    this.sprite.setVisible(false);
    return spot;
  }

  setPosition(x: number, y: number): void {
    const p = clampToBounds(x, y);
    this.s.x = p.x;
    this.s.y = p.y;
    this.syncSprite();
  }

  /** Rifornimento completo: il costo è scalato dal chiamante solo quando ok è true. */
  refuel(cost: number, money: number): { ok: boolean; cost: number } {
    const price = Math.max(0, cost);
    if (money < price) return { ok: false, cost: 0 };
    this.s.fuel = FULL_TANK;
    return { ok: true, cost: price };
  }

  update(dt: number, vec: Point, running: boolean): { x: number; y: number; distance: number; moving: boolean } {
    void running; // I veicoli hanno velocità propria: la corsa del piede non li accelera.
    const kind = this.s.active;
    if (!kind || this.s.fuel <= 0) {
      this.syncSprite();
      return { x: this.s.x, y: this.s.y, distance: 0, moving: false };
    }
    const len = Math.hypot(vec.x, vec.y);
    if (len <= 0.05 || dt <= 0) {
      this.syncSprite();
      return { x: this.s.x, y: this.s.y, distance: 0, moving: false };
    }

    const def = VEHICLE_DEFS[kind];
    const step = def.speed * dt;
    const resolved = this.collision.resolve(this.s.x, this.s.y,
      (vec.x / len) * step, (vec.y / len) * step, def.radius);
    const pos = clampToBounds(resolved.x, resolved.y);
    const distance = Math.hypot(pos.x - this.s.x, pos.y - this.s.y);
    this.s.x = pos.x;
    this.s.y = pos.y;
    this.s.fuel = Math.max(0, this.s.fuel - def.fuelPerSecond * dt);
    this.sprite.setRotation(Math.atan2(vec.y, vec.x));
    this.syncSprite();
    return { x: this.s.x, y: this.s.y, distance, moving: true };
  }

  state(): VehicleSaveState {
    return { owned: [...this.s.owned], active: this.s.active, x: this.s.x, y: this.s.y, fuel: this.s.fuel };
  }

  private applyKind(kind: VehicleKind): void {
    this.sprite.setTexture(kind);
    this.applyOrigin(kind);
    this.sprite.setVisible(true);
  }

  private applyOrigin(kind: VehicleKind): void {
    if (kind === 'motorcycle') this.sprite.setOrigin(0.5, 0.5);
    else this.sprite.setOrigin(0.5, 30 / 40); // Coerente con Traffic.ts per le auto 72x40.
  }

  private syncSprite(): void {
    this.sprite.setPosition(this.s.x * PPM, this.s.y * PPM);
    this.sprite.setDepth(this.s.y * PPM + 1);
  }
}

function clampToBounds(x: number, y: number): Point {
  return {
    x: Math.max(WORLD_BOUNDS.minX, Math.min(WORLD_BOUNDS.maxX, x)),
    y: Math.max(WORLD_BOUNDS.minY, Math.min(WORLD_BOUNDS.maxY, y)),
  };
}
