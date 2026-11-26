export interface Point { x: number; y: number }

export interface WorldMeta {
  generated_utc: string;
  osm_captured_utc: string;
  osm_endpoint: string;
  license: string;
  origin_latlon: [number, number];
  play_radius_m: number;
  pixels_per_meter: number;
}

export interface Road {
  id: string; name: string; kind: string; width_m: number;
  points: [number, number][];
}
export interface Building {
  id: string; name: string; kind: string; levels: number | null;
  footprint: [number, number][]; center: [number, number];
  bbox: [number, number, number, number]; area_m2: number;
}
export interface BuildingSprite {
  id: string; name: string; kind: string; sprite: string;
  anchor_x: number; anchor_y: number; w: number; h: number;
  height_m: number; style: string;
  /** Frazioni dell'immagine corrispondenti al punto di ancoraggio (centro bordo sud, livello strada). */
  origin_x?: number; origin_y?: number;
  wall_h_px?: number; width_px?: number; depth_px?: number;
  /** Finestre dei piani superiori in coordinate locali del generatore: [centro-x, top-y]. */
  windows?: [number, number][];
}
export interface POI {
  id: string; name: string; shop: string; amenity: string;
  railway: string; public_transport: string; highway: string;
  opening_hours?: string;
  x: number; y: number;
}
export interface WorldData {
  meta: WorldMeta;
  roads: Road[];
  rails: { id: string; kind: string; name: string; points: [number, number][] }[];
  platforms: { id: string; footprint: [number, number][] }[];
  buildings: Building[];
  landcover: { kind: string; footprint: [number, number][] }[];
  parking: { footprint: [number, number][] }[];
  barriers: { id: string; kind: string; points: [number, number][] }[];
  pois: POI[];
  colliders: { kind: string; id: string; polygon?: [number, number][]; line?: [number, number][]; width_m?: number }[];
  rail_corridor: [number, number][][];
  stats: Record<string, number>;
}

export interface InteriorDef {
  name: string;
  file: string;
  door: { x: number; y: number; target: string; spawn: [number, number] };
  interactables: { id: string; name: string; x: number; y: number; kind: string }[];
  colliders: [number, number, number, number][];
  size_px: [number, number];
  scale_ppm: number;
}

export interface QuestState {
  id: string; progress: number; done: boolean; accepted: boolean;
}

export interface NeedsState {
  /** Sazietà 0..100; 100 = appena mangiato. */
  hunger: number;
  /** Energia 0..100; 100 = riposato. */
  energy: number;
  /** Minuto assoluto dell'ultimo aggiornamento, per evitare salti dopo il riposo. */
  lastMinute: number;
}

export interface HomeState {
  owned: boolean;
  furniture: { bookshelf: boolean; plant: boolean };
}

export interface JobState {
  active: string | null;
  progress: number;
  target: number;
  pay: number;
  startedMinute: number;
}

export interface TrainState {
  /** Minuto assoluto di scadenza del biglietto EAV (90 minuti di validità). */
  ticketUntil: number;
  riding: boolean;
  rides: number;
}

export interface SaveData {
  version: number;
  savedAt: string;
  player: { x: number; y: number; appearance: string };
  time: { minute: number; day: number };
  money: number;
  inventory: Record<string, number>;
  quests: QuestState[];
  flags: Record<string, boolean>;
  settings: { music: boolean; ambience: boolean; volume: number; showFps: boolean };
  stats: { steps: number; coffees: number; tickets: number; jobs: number; pizzas: number; rides: number };
  needs: NeedsState;
  home: HomeState;
  job: JobState;
  train: TrainState;
}

export interface Interactable {
  id: string;
  label: string;
  x: number; // pixel
  y: number;
  kind: string;
  radius?: number;
  data?: unknown;
}
