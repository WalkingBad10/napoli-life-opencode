/** Standard dimensionale unico e definitivo del progetto (v0.5.0).
 * 1 metro = 16 pixel nel mondo; 48 px/m negli interni; engine_scale = 1. */
export const PPM = 16;
export const SECTOR_M = 64;
export const PLAY_RADIUS_M = 150;
export const WORLD_BOUNDS_PX = PLAY_RADIUS_M * PPM;

export const VERSION = '0.5.0';
export const BUILD_ID = '2026-11-26-LIFE-V05';

export const SAVE_VERSION = 5;

export const PLAYER_SPEED = 2.3;   // m/s camminata (realistica)
export const RUN_SPEED = 4.4;      // m/s corsa
export const NPC_SPEED = 1.15;
export const CAR_SPEED = 6.5;
export const TRAIN_SPEED = 7.0;

export const INTERACT_RADIUS_PX = 52;
export const AUTOSAVE_MS = 60_000;
export const SAVE_KEY = 'napoli-life-opencode-save';

/** Punto di partenza: banchina lato binari, davanti all'ingresso EAV (coordinate locali in metri). */
export const SPAWN = { x: 0, y: -3.2 };

export const COLORS = {
  day: 0xffffff,
  dusk: 0xe8925a,
  night: 0x243456,
  hint: 0xf4ebd6,
};

export const INTERIOR_SCALE = 48; // px/m negli interni (più dettaglio, stanza più piccola)

/** Contratto dimensionale obbligatorio per ogni mappa futura. */
export const STANDARD = {
  world_ppm: 16,
  interior_ppm: 48,
  engine_scale: 1,
  sector_m: 64,
  sector_px: 1024,
  character_frame: [16, 32] as const,
  character_sheet: [64, 128] as const,
  feet_y: 30,
  window: [12, 16] as const,
  window_step: [38, 46] as const,
  door: [22, 38] as const,
  floor_px: 46,
  car: [72, 40] as const,
  bus: [112, 44] as const,
  scooter: [52, 34] as const,
  train: [576, 56] as const,
  lamp: [24, 76] as const,
  bench: [56, 26] as const,
  bin: [20, 26] as const,
  tree: [64, 88] as const,
  planter: [32, 20] as const,
  ticket_machine: [20, 40] as const,
  interior_room: [576, 384] as const,
  sidewalk_m: [1.5, 2.0] as const,
  rail_sleeper_px: 12,
} as const;

/** Orari simulati: OSM non riporta opening_hours per queste attività. */
export const BUSINESS_HOURS: Record<string, { open: number; close: number; label: string }> = {
  station: { open: 5 * 60 + 30, close: 23 * 60 + 30, label: 'Stazione Circumflegrea' },
  bar: { open: 7 * 60, close: 21 * 60, label: 'Bar / Pizzeria Donna Rosa' },
  shop: { open: 8 * 60, close: 20 * 60, label: 'Negozio di quartiere' },
  pizzeria: { open: 11 * 60, close: 22 * 60 + 30, label: 'Pizzeria Carpe Diem' },
  home: { open: 0, close: 24 * 60, label: 'Abitazione' },
};

/** Menu con effetti sui bisogni. I prezzi sono in euro. */
export const MENU: Record<string, { name: string; price: number; hunger: number; energy: number }> = {
  caffe: { name: 'Espresso', price: 1.2, hunger: 5, energy: 10 },
  dolce: { name: 'Dolce napoletano', price: 2.0, hunger: 18, energy: 4 },
  bevanda: { name: 'Bevanda fresca', price: 1.5, hunger: 12, energy: 6 },
  pizza: { name: 'Pizza al taglio', price: 4.5, hunger: 38, energy: 8 },
  acqua: { name: 'Acqua naturale', price: 0.7, hunger: 4, energy: 5 },
};

export const HOME_FURNITURE: Record<string, { name: string; price: number }> = {
  bookshelf: { name: 'Libreria', price: 14 },
  plant: { name: 'Pianta in vaso', price: 7 },
};

export const JOB_DEFS: Record<string, { name: string; target: number; pay: number; item: string }> = {
  bar: { name: 'Servi tre espressi al bar', target: 3, pay: 12, item: 'caffe' },
  pizzeria: { name: 'Prepara tre pizze al taglio', target: 3, pay: 18, item: 'pizza' },
};
