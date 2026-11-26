import { MENU } from '../config';
import type { NeedsState, SaveData } from '../types';

/** Bisogni discreti: non bloccano il gioco, ma danno un ritmo alla giornata. */
export class NeedsSystem {
  state: NeedsState;

  constructor(save: SaveData) {
    this.state = save.needs;
  }

  /** Chiamato a ogni minuto di gioco. I salti enormi (es. import) non prosciugano il personaggio. */
  update(absoluteMinute: number, awake = true): void {
    const delta = Math.min(1440, Math.max(0, absoluteMinute - this.state.lastMinute));
    if (delta > 0) {
      this.state.hunger = clamp(this.state.hunger - delta / 14);
      this.state.energy = clamp(this.state.energy - delta / (awake ? 18 : 12));
    }
    this.state.lastMinute = absoluteMinute;
  }

  eat(item: string): boolean {
    const entry = MENU[item];
    if (!entry) return false;
    this.state.hunger = clamp(this.state.hunger + entry.hunger);
    this.state.energy = clamp(this.state.energy + entry.energy);
    return true;
  }

  /** Riposo: l'energia torna rapidamente, la fame aumenta lentamente. */
  afterSleep(minutes: number, absoluteMinute: number): void {
    this.state.energy = clamp(this.state.energy + minutes * 0.55);
    this.state.hunger = clamp(this.state.hunger - minutes * 0.06);
    this.state.lastMinute = absoluteMinute;
  }

  get status(): string {
    if (this.state.energy < 25) return 'Stanco';
    if (this.state.hunger < 25) return 'Affamato';
    if (this.state.hunger > 80 && this.state.energy > 80) return 'In forma';
    return 'Normale';
  }

  write(save: SaveData): void { save.needs = { ...this.state }; }
}

function clamp(v: number): number {
  return Math.max(0, Math.min(100, Math.round(v * 10) / 10));
}
