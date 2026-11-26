import Phaser from 'phaser';

export interface SectorOrigin { x: number; y: number }

interface SectorEntry {
  x: number;
  y: number;
  key: string;
  requested: boolean;
  loaded: boolean;
  image: Phaser.GameObjects.Image | null;
}

/** Caricamento dei settori del suolo solo quando entrano nella vista: nessuna API esterna. */
export class SectorStreamer {
  private readonly origins: SectorOrigin[];
  private readonly entries = new Map<string, SectorEntry>();

  constructor(private scene: Phaser.Scene, origins: SectorOrigin[], private baseUrl: string,
              private sectorM = 64, private ppm = 16) {
    this.origins = origins.map(o => ({ x: o.x, y: o.y }));

    // Un solo listener per istanza: lo sprite viene creato appena la texture è pronta.
    this.scene.load.on('filecomplete', (key: string) => this.onFileComplete(key));
    this.scene.load.on('loaderror', (file: Phaser.Loader.File) => {
      const key = file?.key ?? '';
      const entry = this.entries.get(key);
      if (!entry) return;
      entry.requested = false;
      console.warn(`[SectorStreamer] caricamento fallito: ${key}`);
    });
  }

  /** Richiede un settore per una posizione in metri; riusa le texture già precaricate dal Boot. */
  ensure(x: number, y: number): void {
    const sx = this.sectorOf(x);
    const sy = this.sectorOf(y);
    if (!this.origins.some(o => this.sectorOf(o.x) === sx && this.sectorOf(o.y) === sy)) return;

    const key = this.key(sx, sy);
    let entry = this.entries.get(key);
    if (!entry) {
      entry = { x: sx, y: sy, key, requested: false, loaded: false, image: null };
      this.entries.set(key, entry);
    }
    if (this.scene.textures.exists(key)) {
      entry.loaded = true;
      this.createImage(entry);
      return;
    }
    if (entry.requested) return;
    entry.requested = true;
    try {
      this.scene.load.image(key, `${this.baseUrl}assets/tiles/${key}.png`);
      if (!this.scene.load.isLoading()) this.scene.load.start();
    } catch (e) {
      entry.requested = false;
      console.warn(`[SectorStreamer] richiesta fallita: ${key}`, e);
    }
  }

  /** Mostra i settori che intersecano la vista (in pixel) e scarica quelli lontani. */
  update(view: Phaser.Geom.Rectangle): void {
    const size = this.sectorM * this.ppm;
    const cx = Math.floor(view.centerX / size);
    const cy = Math.floor(view.centerY / size);
    const visible = new Set<string>();

    for (const origin of this.origins) {
      const sx = this.sectorOf(origin.x);
      const sy = this.sectorOf(origin.y);
      const rect = new Phaser.Geom.Rectangle(sx * this.ppm, sy * this.ppm, size, size);
      if (!Phaser.Geom.Intersects.RectangleToRectangle(view, rect)) continue;
      const key = this.key(sx, sy);
      visible.add(key);
      this.ensure(sx, sy);
    }

    for (const [key, entry] of this.entries) {
      if (entry.image) entry.image.setVisible(visible.has(key));
      if (visible.has(key) || entry.requested) continue;
      // Culling a distanza di Chebyshev: si conserva anche il bordo dei settori appena usati.
      const dx = Math.abs(entry.x / this.sectorM - cx);
      const dy = Math.abs(entry.y / this.sectorM - cy);
      if (Math.max(dx, dy) > 3) {
        this.unload(entry);
        this.entries.delete(key);
      }
    }
  }

  stats(): { loaded: number; pending: number; total: number } {
    let loaded = 0;
    let pending = 0;
    for (const entry of this.entries.values()) {
      if (entry.requested) pending++;
      else if (entry.loaded) loaded++;
    }
    return { loaded, pending, total: this.origins.length };
  }

  preloadAt(x: number, y: number, radiusSectors = 1): void {
    const cx = Math.floor(x / this.sectorM);
    const cy = Math.floor(y / this.sectorM);
    for (let dx = -radiusSectors; dx <= radiusSectors; dx++) {
      for (let dy = -radiusSectors; dy <= radiusSectors; dy++) {
        this.ensure((cx + dx) * this.sectorM, (cy + dy) * this.sectorM);
      }
    }
  }

  private onFileComplete(key: string): void {
    const entry = this.entries.get(key);
    if (!entry) return;
    entry.requested = false;
    if (!this.scene.textures.exists(key)) return;
    entry.loaded = true;
    this.createImage(entry);
  }

  private createImage(entry: SectorEntry): void {
    if (entry.image && entry.image.active) return;
    if (!this.scene.textures.exists(entry.key)) return;
    entry.image = this.scene.add.image(entry.x * this.ppm, entry.y * this.ppm, entry.key)
      .setOrigin(0, 0).setDepth(-1000);
  }

  private unload(entry: SectorEntry): void {
    if (entry.image) {
      entry.image.destroy();
      entry.image = null;
    }
    entry.loaded = false;
    if (this.scene.textures.exists(entry.key)) this.scene.textures.remove(entry.key);
  }

  private sectorOf(value: number): number {
    return Math.floor(value / this.sectorM) * this.sectorM;
  }

  private key(x: number, y: number): string {
    return `sector_${x}_${y}`;
  }
}
