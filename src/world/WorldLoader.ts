import type { BuildingSprite, InteriorDef, WorldData } from '../types';

const url = (path: string) => `${import.meta.env.BASE_URL}${path}`;

/** Carica i dati cartografici già convertiti: nessuna chiamata API a runtime. */
export class WorldLoader {
  static async load(): Promise<{ world: WorldData; buildings: BuildingSprite[]; interiors: Record<string, InteriorDef> }> {
    const [worldRes, buildingsRes, interiorsRes] = await Promise.all([
      fetch(url('data/world/pianura_world.json')),
      fetch(url('assets/buildings/manifest.json')),
      fetch(url('assets/interiors/manifest.json')),
    ]);
    if (!worldRes.ok || !buildingsRes.ok || !interiorsRes.ok) {
      throw new Error(`Caricamento dati fallito: ${worldRes.status}/${buildingsRes.status}/${interiorsRes.status}`);
    }
    const [world, buildings, interiors] = await Promise.all([
      worldRes.json() as Promise<WorldData>,
      buildingsRes.json() as Promise<BuildingSprite[]>,
      interiorsRes.json() as Promise<Record<string, InteriorDef>>,
    ]);
    return { world, buildings, interiors };
  }

  static asset(path: string): string { return url(path); }
}
