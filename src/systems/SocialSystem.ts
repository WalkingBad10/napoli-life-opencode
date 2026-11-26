/** Relazioni con gli NPC: i valori sono memorizzati nello stato passato al costruttore. */
export interface Relationship {
  friendship: number;
  romance: number;
  gifts: number;
  lastGiftDay: number;
  /** Giorno dell'ultima chiacchierata: distinto dal regalo, così coesistono. */
  lastTalkDay?: number;
}

export const GIFT_VALUES: Record<string, number> = {
  caffe: 4, dolce: 6, bevanda: 3, pizza: 10, acqua: 2, fiore: 16, libro: 12,
};

const EMPTY: Relationship = { friendship: 0, romance: 0, gifts: 0, lastGiftDay: -1, lastTalkDay: -1 };
const GIFT_ITEMS = ['fiore', 'libro'];

export class SocialSystem {
  private readonly rel: Record<string, Relationship>;

  constructor(state: Record<string, Relationship>) { this.rel = state; }

  get(id: string): Relationship {
    let r = this.rel[id];
    if (!r) {
      r = { ...EMPTY };
      this.rel[id] = r;
    }
    return r;
  }

  /** Una chiacchierata al giorno; l'affetto cresce solo dopo aver stretto amicizia. */
  talk(id: string, day: number): { friendship: number; romance: number; level: string } {
    const r = this.get(id);
    if (r.lastTalkDay !== day) {
      r.friendship = clamp(r.friendship + 1);
      if (r.friendship >= 20) r.romance = clamp(r.romance + 0.5);
      r.lastTalkDay = day;
    }
    return { friendship: r.friendship, romance: r.romance, level: this.level(id) };
  }

  /** Consuma un oggetto dall'inventario: fiore e libro valgono anche metà in romance. */
  gift(id: string, item: string, day: number, items: Record<string, number>):
      { ok: boolean; friendship: number; romance: number; reason?: string } {
    const r = this.get(id);
    if (r.lastGiftDay === day) {
      return { ok: false, friendship: r.friendship, romance: r.romance,
        reason: 'Hai già interagito oggi con questa persona' };
    }
    const value = GIFT_VALUES[item];
    if (!value || (items[item] ?? 0) < 1) {
      return { ok: false, friendship: r.friendship, romance: r.romance,
        reason: 'Oggetto non disponibile' };
    }
    items[item] = (items[item] ?? 0) - 1;
    r.friendship = clamp(r.friendship + value);
    r.romance = clamp(r.romance + (GIFT_ITEMS.includes(item) ? value / 2 : 0));
    r.gifts += 1;
    r.lastGiftDay = day;
    return { ok: true, friendship: r.friendship, romance: r.romance };
  }

  /** Copie di lettura: nessuna modifica può arrivare dall'esterno allo stato condiviso. */
  all(): [string, Relationship][] {
    return Object.entries(this.rel).map(([id, r]) => [id, { ...r }]);
  }

  level(id: string): string {
    const r = this.rel[id] ?? EMPTY;
    if (r.friendship >= 60 && r.romance >= 40) return 'fidanzato';
    if (r.friendship >= 35) return 'stretto';
    if (r.friendship >= 15) return 'amico';
    return 'conoscente';
  }
}

function clamp(v: number): number {
  return Math.max(0, Math.min(100, Math.round(v * 10) / 10));
}
