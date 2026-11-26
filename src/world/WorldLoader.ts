import type { BuildingSprite, InteriorDef, WorldData } from '../types';

const url = (path: string) => `${import.meta.env.BASE_URL}${path}`;

export interface TilesManifest {
  version?: string;
  sector_m: number;
  sector_px: number;
  /** I generatori 0.6 scrivono coppie; le versioni precedenti avevano un array piatto. */
  origins: [number, number][] | number[];
  bounds?: { minX: number; minY: number; maxX: number; maxY: number };
  count?: number;
  engine_scale?: number;
}

/** Normalizza il manifest settori: accetta sia [[x,y],…] sia [x,y,x,y,…]. */
export function tileOrigins(manifest: TilesManifest): [number, number][] {
  const out: [number, number][] = [];
  for (const item of manifest.origins ?? []) {
    if (Array.isArray(item) && item.length >= 2) out.push([Number(item[0]), Number(item[1])]);
  }
  if (out.length) return out;
  const flat = manifest.origins as number[];
  for (let i = 0; i + 1 < flat.length; i += 2) out.push([Number(flat[i]), Number(flat[i + 1])]);
  return out.filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
}

export interface SpriteManifestEntry {
  name: string;
  file: string;
  type?: string;
  [key: string]: unknown;
}

export interface SpritesManifest {
  version?: string;
  characters?: string[];
  sprites?: Record<string, SpriteManifestEntry>;
}

export interface AudioManifest { version?: string; files: string[] }

/** Carica i dati cartografici già convertiti: nessuna chiamata API a runtime. */
export class WorldLoader {
  static async load(): Promise<{
    world: WorldData;
    buildings: BuildingSprite[];
    interiors: Record<string, InteriorDef>;
    tiles: TilesManifest;
    sprites: SpritesManifest;
    audio: AudioManifest;
  }> {
    const [worldRes, buildingsRes, interiorsRes, tilesRes, spritesRes, audioRes] = await Promise.all([
      fetch(url('data/world/pianura_world.json')),
      fetch(url('assets/buildings/manifest.json')),
      fetch(url('assets/interiors/manifest.json')),
      fetch(url('assets/tiles/manifest.json')),
      fetch(url('assets/sprites/manifest.json')),
      fetch(url('assets/audio/manifest.json')),
    ]);
    if ([worldRes, buildingsRes, interiorsRes, tilesRes, spritesRes, audioRes].some(r => !r.ok)) {
      throw new Error(`Caricamento dati fallito: ${[worldRes, buildingsRes, interiorsRes, tilesRes, spritesRes, audioRes].map(r => r.status).join('/')}`);
    }
    const [world, buildings, interiors, tiles, sprites, audio] = await Promise.all([
      worldRes.json() as Promise<WorldData>,
      buildingsRes.json() as Promise<BuildingSprite[]>,
      interiorsRes.json() as Promise<Record<string, InteriorDef>>,
      tilesRes.json() as Promise<TilesManifest>,
      spritesRes.json() as Promise<SpritesManifest>,
      audioRes.json() as Promise<AudioManifest>,
    ]);
    return { world, buildings, interiors, tiles, sprites, audio };
  }

  static asset(path: string): string { return url(path); }
}
