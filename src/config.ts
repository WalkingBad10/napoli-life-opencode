/** Standard dimensionale unico e definitivo del progetto (v0.6.0).
 * 1 metro = 16 pixel nel mondo; 48 px/m negli interni; engine_scale = 1. */
export const PPM = 16;
export const SECTOR_M = 64;
/** Area rettangolare derivata dal dump OSM esteso: 960 x 1024 m. */
export const WORLD_BOUNDS = { minX: -256, minY: -320, maxX: 704, maxY: 704 } as const;
/** Compatibilità con le API v0.5: raggio indicativo, i limiti veri sono WORLD_BOUNDS. */
export const PLAY_RADIUS_M = 480;
export const WORLD_BOUNDS_PX = {
  left: WORLD_BOUNDS.minX * PPM,
  top: WORLD_BOUNDS.minY * PPM,
  width: (WORLD_BOUNDS.maxX - WORLD_BOUNDS.minX) * PPM,
  height: (WORLD_BOUNDS.maxY - WORLD_BOUNDS.minY) * PPM,
};

export const VERSION = '0.6.0';
export const BUILD_ID = '2026-11-26-LIFE-V06';

export const SAVE_VERSION = 6;

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
  supermarket: { open: 8 * 60, close: 21 * 60, label: 'Supermercato Conad / Coop' },
  tobacco: { open: 7 * 60 + 30, close: 20 * 60, label: 'Tabaccheria di quartiere' },
  bookmaker: { open: 10 * 60, close: 22 * 60, label: "Scommesse d'oro (fittizia)" },
  real_bookmaker: { open: 9 * 60, close: 22 * 60, label: 'Centro scommesse OSM' },
  bakery: { open: 6 * 60 + 30, close: 19 * 60 + 30, label: 'Forno / panetteria' },
  clothing: { open: 9 * 60 + 30, close: 20 * 60 + 30, label: 'Negozio di abbigliamento' },
  workshop: { open: 8 * 60, close: 18 * 60 + 30, label: 'Officina meccanica' },
  dealership: { open: 9 * 60, close: 19 * 60, label: 'Autonetwork — veicoli' },
  fuel: { open: 0, close: 24 * 60, label: 'Distributore IP' },
  home: { open: 0, close: 24 * 60, label: 'Abitazione' },
};

/** Menu con effetti sui bisogni. I prezzi sono in euro. */
export const MENU: Record<string, { name: string; price: number; hunger: number; energy: number }> = {
  caffe: { name: 'Espresso', price: 1.2, hunger: 5, energy: 10 },
  dolce: { name: 'Dolce napoletano', price: 2.0, hunger: 18, energy: 4 },
  bevanda: { name: 'Bevanda fresca', price: 1.5, hunger: 12, energy: 6 },
  pizza: { name: 'Pizza al taglio', price: 4.5, hunger: 38, energy: 8 },
  acqua: { name: 'Acqua naturale', price: 0.7, hunger: 4, energy: 5 },
  cornetto: { name: 'Cornetto', price: 1.8, hunger: 22, energy: 6 },
  panino: { name: 'Panino', price: 3.2, hunger: 30, energy: 9 },
  frutta: { name: 'Frutta di stagione', price: 1.1, hunger: 12, energy: 4 },
  spesa: { name: 'Spesa settimanale', price: 12, hunger: 30, energy: 4 },
  sigarette: { name: 'Sigarette', price: 4.5, hunger: 0, energy: 0 },
  tabacco: { name: 'Tabacco', price: 6, hunger: 0, energy: 0 },
  attrezzi: { name: 'Attrezzi da officina', price: 18, hunger: 0, energy: 0 },
  fiore: { name: 'Fiore', price: 6, hunger: 0, energy: 0 },
  libro: { name: 'Libro', price: 9, hunger: 0, energy: 0 },
};

export const HOME_FURNITURE: Record<string, { name: string; price: number }> = {
  bookshelf: { name: 'Libreria', price: 14 },
  plant: { name: 'Pianta in vaso', price: 7 },
  tv: { name: 'Televisore', price: 55 },
  sofa: { name: 'Divano', price: 80 },
};

export const JOB_DEFS: Record<string, { name: string; target: number; pay: number; item: string }> = {
  bar: { name: 'Servi tre espressi al bar', target: 3, pay: 12, item: 'caffe' },
  pizzeria: { name: 'Prepara tre pizze al taglio', target: 3, pay: 18, item: 'pizza' },
  supermarket: { name: 'Sistema tre cassette alla cassa', target: 3, pay: 14, item: 'spesa' },
  bakery: { name: 'Vendi tre cornetti al forno', target: 3, pay: 13, item: 'cornetto' },
  workshop: { name: 'Controlla tre motociclette in officina', target: 3, pay: 22, item: 'attrezzi' },
  tobacco: { name: 'Aiuta in tabaccheria', target: 2, pay: 10, item: 'sigarette' },
};

/** Prezzo dei servizi e dei regali usati nelle nuove attività. */
export const SERVICE_PRICES = {
  refuel: 24,
  giftFlower: 6,
  giftBook: 9,
  rentDeposit: 160,
  secondHome: 450,
} as const;
