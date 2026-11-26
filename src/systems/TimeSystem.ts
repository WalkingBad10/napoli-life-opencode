import type { SaveData } from '../types';

export type DayPhase = 'dawn' | 'day' | 'dusk' | 'night';

/** Un minuto di gioco ogni 500 ms: una giornata dura 12 minuti reali. */
export class TimeSystem {
  minute: number;
  day: number;
  private accumulator = 0;

  constructor(save: SaveData) {
    this.minute = save.time.minute;
    this.day = save.time.day;
  }

  update(deltaMs: number): boolean {
    this.accumulator += deltaMs;
    let changed = false;
    while (this.accumulator >= 500) {
      this.accumulator -= 500;
      this.minute = (this.minute + 1) % 1440;
      if (this.minute === 0) this.day += 1;
      changed = true;
    }
    return changed;
  }

  get hour(): number { return Math.floor(this.minute / 60); }
  get minuteOfHour(): number { return this.minute % 60; }
  get clock(): string {
    return `${String(this.hour).padStart(2, '0')}:${String(this.minuteOfHour).padStart(2, '0')}`;
  }

  get phase(): DayPhase {
    const h = this.hour;
    if (h >= 5 && h < 7) return 'dawn';
    if (h >= 7 && h < 18) return 'day';
    if (h >= 18 && h < 21) return 'dusk';
    return 'night';
  }

  /** Fattore 0 (pieno giorno) .. 1 (notte fonda), usato per la tinta della telecamera. */
  get darkness(): number {
    const h = this.hour + this.minuteOfHour / 60;
    if (h < 5) return 0.72;
    if (h < 7) return 0.72 - (h - 5) * 0.32;
    if (h < 18) return 0;
    if (h < 21) return (h - 18) * 0.22;
    return 0.66;
  }

  get populationFactor(): number {
    const h = this.hour;
    if (h >= 7 && h <= 9) return 1.0;   // pendolari
    if (h >= 12 && h <= 14) return 0.85;
    if (h >= 17 && h <= 19) return 1.0;
    if (h >= 21 || h < 6) return 0.25;
    return 0.6;
  }

  write(save: SaveData): void {
    save.time = { minute: this.minute, day: this.day };
  }
}
