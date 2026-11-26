import Phaser from 'phaser';
import { CAR_SPEED, PPM, TRAIN_SPEED } from '../config';
import type { Point, Road, WorldData } from '../types';

/** Veicoli e treno EAV: si muovono sui tracciati OSM, con profondità coerente. */
export class Vehicle {
  sprite: Phaser.GameObjects.Sprite;
  private t = 0;
  /** Il treno può essere guidato dal giocatore: in manual mode non avanza da solo. */
  manual = false;
  private paused = false;

  constructor(scene: Phaser.Scene, private path: Point[], private textureName: string,
              private speed = CAR_SPEED, startT = 0, scale = 1) {
    const p = this.at(startT);
    this.t = startT;
    this.sprite = scene.add.sprite(p.x * PPM, p.y * PPM, textureName);
    // Origini coerenti con la metrica: auto 72x40 -> (36,30), bus 112x44 -> (56,34), treno centro.
    if (textureName === 'train_eav') this.sprite.setOrigin(0.5, 0.5);
    else if (textureName === 'bus') this.sprite.setOrigin(0.5, 34 / 44);
    else this.sprite.setOrigin(0.5, 30 / 40);
    this.sprite.setScale(scale);
  }

  get progress(): number { return this.t; }
  set progress(value: number) { this.t = ((value % 1) + 1) % 1; this.sync(); }
  get velocity(): number { return this.speed; }
  set velocity(value: number) { this.speed = Math.max(0, value); }
  get lengthMeters(): number { return this.pathLength(); }
  get position(): Point { return this.at(this.t); }
  setPaused(value: boolean): void { this.paused = value; }

  private at(t: number): Point {
    const n = this.path.length;
    if (n < 2) return this.path[0] ?? { x: 0, y: 0 };
    const f = ((t % 1) + 1) % 1 * (n - 1);
    const i = Math.min(n - 2, Math.floor(f));
    const k = f - i;
    return {
      x: this.path[i].x + (this.path[i + 1].x - this.path[i].x) * k,
      y: this.path[i].y + (this.path[i + 1].y - this.path[i].y) * k,
    };
  }

  private sync(): void {
    const p = this.at(this.t);
    this.sprite.setPosition(p.x * PPM, p.y * PPM);
    // Il treno è disegnato di lato: ruotarlo crea deformazioni. I veicoli visti dall'alto sì.
    if (this.textureName === 'train_eav') this.sprite.setRotation(0);
    else {
      const ahead = this.at(this.t + 0.002);
      this.sprite.setRotation(Math.atan2(ahead.y - p.y, ahead.x - p.x));
    }
    this.sprite.setDepth(p.y * PPM + 1);
    this.sprite.setVisible(Math.abs(p.x) < 220 && Math.abs(p.y) < 180);
  }

  update(deltaSec: number, active: boolean): void {
    if (!active || this.paused) return;
    if (!this.manual) this.t += (this.speed * deltaSec) / Math.max(1, this.pathLength());
    this.sync();
  }

  private pathLength(): number {
    let n = 0;
    for (let i = 1; i < this.path.length; i++) {
      n += Math.hypot(this.path[i].x - this.path[i - 1].x, this.path[i].y - this.path[i - 1].y);
    }
    return n;
  }
}

function toPoints(road: Road): Point[] {
  return road.points.map(([x, y]) => ({ x, y }));
}

export function createTraffic(scene: Phaser.Scene, world: WorldData): { vehicles: Vehicle[]; train: Vehicle } {
  const vehicles: Vehicle[] = [];
  const candidates = world.roads.filter(r =>
    ['residential', 'tertiary', 'secondary', 'unclassified', 'service'].includes(r.kind) &&
    r.points.length >= 2 && r.points.some(([x, y]) => Math.abs(x) < 140 && Math.abs(y) < 140));

  // Sensi di marcia alternati e velocità diverse: il traffico non è un trenino sincronizzato.
  const chosen = [0, 1, 2, 3].map(i => candidates[(i * 5 + 2) % candidates.length]).filter(Boolean);
  const textures = ['car_red', 'car_silver', 'car_red', 'bus'];
  chosen.forEach((road, i) => {
    const path = i % 2 ? [...toPoints(road)].reverse() : toPoints(road);
    const vehicle = new Vehicle(scene, path, textures[i % textures.length],
      i === 3 ? 4.2 : CAR_SPEED - i * 0.55, i * 0.23, i === 3 ? 0.85 : 1);
    vehicles.push(vehicle);
  });

  // Il treno segue i punti binario OSM ordinati lungo l'asse est-ovest.
  const railPoints: Point[] = [];
  for (const rail of world.rails) {
    if (rail.kind !== 'rail') continue;
    for (const [x, y] of rail.points) {
      if (Math.abs(x) < 220 && Math.abs(y) < 25 && !railPoints.some(p => Math.abs(p.x - x) < 1 && Math.abs(p.y - y) < 1)) {
        railPoints.push({ x, y });
      }
    }
  }
  railPoints.sort((a, b) => a.x - b.x);
  const trainPath = railPoints.length > 1 ? railPoints : [{ x: -160, y: 6 }, { x: 160, y: -6 }];
  const train = new Vehicle(scene, trainPath, 'train_eav', TRAIN_SPEED, 0.1, 1);
  train.sprite.setDepth(7 * PPM);
  return { vehicles, train };
}
