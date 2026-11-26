/** Standard dimensionale unico del progetto. 1 metro = 16 pixel. */
export const PPM = 16;
export const SECTOR_M = 64;
export const PLAY_RADIUS_M = 150;
export const WORLD_BOUNDS_PX = PLAY_RADIUS_M * PPM;

export const VERSION = '0.2.0';
export const BUILD_ID = '2026-11-26';

export const PLAYER_SPEED = 2.3;   // m/s camminata (realistica)
export const RUN_SPEED = 4.4;      // m/s corsa
export const NPC_SPEED = 1.15;
export const CAR_SPEED = 6.5;

export const INTERACT_RADIUS_PX = 52;
export const AUTOSAVE_MS = 60_000;
export const SAVE_KEY = 'napoli-life-opencode-save';
export const SAVE_VERSION = 3;

/** Punto di partenza: marciapiede davanti al fabbricato viaggiatori (coordinate locali in metri). */
export const SPAWN = { x: 0, y: -26 };

export const COLORS = {
  day: 0xffffff,
  dusk: 0xe8925a,
  night: 0x243456,
  hint: 0xf4ebd6,
};

export const INTERIOR_SCALE = 48; // px/m negli interni (più dettaglio, stanza più piccola)
