import { JOB_DEFS } from '../config';
import type { JobState, SaveData } from '../types';

/** Lavori brevi e retribuiti: nessun conto alla rovescia invasivo, solo turni di mezz'ora. */
export class JobSystem {
  state: JobState;

  constructor(save: SaveData) { this.state = save.job; }

  accept(id: string, minute: number): boolean {
    const def = JOB_DEFS[id];
    if (!def || this.state.active) return false;
    this.state.active = id;
    this.state.progress = 0;
    this.state.target = def.target;
    this.state.pay = def.pay;
    this.state.startedMinute = minute;
    return true;
  }

  /** Ritorna true solo quando il turno viene completato adesso. */
  contribute(id: string, item: string): 'none' | 'progress' | 'done' {
    if (this.state.active !== id) return 'none';
    const def = JOB_DEFS[id];
    if (!def || def.item !== item || this.state.progress >= this.state.target) return 'none';
    this.state.progress++;
    return this.state.progress >= this.state.target ? 'done' : 'progress';
  }

  /** Un turno resta valido per 120 minuti di gioco; poi si chiude senza penali. */
  expire(minute: number): boolean {
    if (!this.state.active) return false;
    if (minute - this.state.startedMinute < 120 && minute >= this.state.startedMinute) return false;
    this.abandon();
    return true;
  }

  abandon(): void {
    this.state.active = null;
    this.state.progress = 0;
    this.state.target = 0;
    this.state.pay = 0;
    this.state.startedMinute = 0;
  }

  get label(): string {
    return this.state.active ? JOB_DEFS[this.state.active]?.name ?? 'Lavoro' : '';
  }

  get progressText(): string {
    return this.state.active ? `${this.state.progress}/${this.state.target}` : '';
  }

  write(save: SaveData): void { save.job = { ...this.state }; }
}
