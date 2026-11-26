import { WORLD_BOUNDS } from '../config';
import type { WorldData } from '../types';

const CELL_M = 32;
const cellKey = (cx: number, cy: number) => `${cx}:${cy}`;

interface ColliderEntry {
  kind: string;
  polygon?: [number, number][];
  line?: [number, number][];
  width: number;
  minX: number; minY: number; maxX: number; maxY: number;
}

function inside(x: number, y: number, poly: [number, number][]): boolean {
  let hit = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
}

function distToSegment(px: number, py: number, ax: number, ay: number, bx: number, by: number): number {
  const dx = bx - ax, dy = by - ay;
  const len2 = dx * dx + dy * dy;
  if (len2 === 0) return Math.hypot(px - ax, py - ay);
  let t = ((px - ax) * dx + (py - ay) * dy) / len2;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

/** Collisioni vettoriali in metri: perimetri edifici OSM + recinzioni + limiti area. */
export class CollisionWorld {
  /** Broadphase a celle da 32 m: l'area v0.6 ha centinaia di collider. */
  private grid = new Map<string, ColliderEntry[]>();

  constructor(world: WorldData) {
    for (const c of world.colliders) {
      const pts = c.polygon ?? c.line;
      if (!pts || pts.length < 2) continue;
      const xs = pts.map(p => p[0]);
      const ys = pts.map(p => p[1]);
      const entry: ColliderEntry = {
        kind: c.kind,
        polygon: c.polygon,
        line: c.line,
        width: c.kind === 'building' ? 0.32 : (c.width_m ?? 0.4) / 2 + 0.2,
        minX: Math.min(...xs), minY: Math.min(...ys),
        maxX: Math.max(...xs), maxY: Math.max(...ys),
      };
      const pad = 2.2;
      for (let cx = Math.floor((entry.minX - pad) / CELL_M); cx <= Math.floor((entry.maxX + pad) / CELL_M); cx++) {
        for (let cy = Math.floor((entry.minY - pad) / CELL_M); cy <= Math.floor((entry.maxY + pad) / CELL_M); cy++) {
          const key = cellKey(cx, cy);
          const bucket = this.grid.get(key);
          if (bucket) bucket.push(entry); else this.grid.set(key, [entry]);
        }
      }
    }
  }

  blocked(x: number, y: number, radius = 0.25): boolean {
    if (x < WORLD_BOUNDS.minX + radius || x > WORLD_BOUNDS.maxX - radius ||
        y < WORLD_BOUNDS.minY + radius || y > WORLD_BOUNDS.maxY - radius) return true;
    const pad = radius + 2.2;
    const candidates = new Set<ColliderEntry>();
    for (let cx = Math.floor((x - pad) / CELL_M); cx <= Math.floor((x + pad) / CELL_M); cx++) {
      for (let cy = Math.floor((y - pad) / CELL_M); cy <= Math.floor((y + pad) / CELL_M); cy++) {
        for (const c of this.grid.get(cellKey(cx, cy)) ?? []) candidates.add(c);
      }
    }
    for (const c of candidates) {
      if (x < c.minX - 1 || x > c.maxX + 1 || y < c.minY - 1 || y > c.maxY + 1) continue;
      if (c.polygon) {
        if (inside(x, y, c.polygon)) return true;
        for (let i = 0; i < c.polygon.length; i++) {
          const a = c.polygon[i], b = c.polygon[(i + 1) % c.polygon.length];
          if (distToSegment(x, y, a[0], a[1], b[0], b[1]) < radius) return true;
        }
      } else if (c.line) {
        for (let i = 0; i < c.line.length - 1; i++) {
          const a = c.line[i], b = c.line[i + 1];
          if (distToSegment(x, y, a[0], a[1], b[0], b[1]) < radius + c.width) return true;
        }
      }
    }
    return false;
  }

  /** Prova X e Y separatamente per consentire lo scorrimento lungo i muri. */
  resolve(currentX: number, currentY: number, dx: number, dy: number, radius = 0.25): { x: number; y: number } {
    let x = currentX, y = currentY;
    if (!this.blocked(x + dx, y, radius)) x += dx;
    if (!this.blocked(x, y + dy, radius)) y += dy;
    return { x, y };
  }
}
