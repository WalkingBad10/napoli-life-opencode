import { BUSINESS_HOURS } from '../config';
import type { SaveData } from '../types';

/** Orari di apertura simulati: OSM non fornisce opening_hours per questi POI. */
export class BusinessSystem {
  /** Una porta chiusa non blocca mai l'uscita: la chiusura vale solo per gli ingressi dal mondo. */
  isOpen(id: string, minute: number): boolean {
    if (id === 'home') return true;
    const h = BUSINESS_HOURS[id];
    if (!h) return true;
    if (h.open <= h.close) return minute >= h.open && minute < h.close;
    return minute >= h.open || minute < h.close; // es. attività notturna
  }

  label(id: string): string {
    return BUSINESS_HOURS[id]?.label ?? id;
  }

  hoursLabel(id: string): string {
    const h = BUSINESS_HOURS[id];
    if (!h) return 'Orari non noti';
    const fmt = (m: number) => `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;
    return `${fmt(h.open)}–${fmt(h.close)}`;
  }

  closedMessage(id: string): string {
    return `${this.label(id)} è chiuso. Orari: ${this.hoursLabel(id)}.`;
  }

  write(_save: SaveData): void {
    // Gli orari sono deterministici dal clock: nessuno stato persistente aggiuntivo.
  }
}
