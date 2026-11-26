import type { QuestState, SaveData } from '../types';

export interface QuestDef {
  id: string;
  title: string;
  description: string;
  steps: string[];
  reward: number;
}

export const QUEST_DEFS: QuestDef[] = [
  {
    id: 'caffe', title: 'Un caffè a Pianura',
    description: 'Entra nel bar vicino alla stazione e ordina un espresso al barista.',
    steps: ['Parla con il barista', 'Acquista un espresso (€ 1,20)'],
    reward: 0,
  },
  {
    id: 'biglietto', title: 'Il biglietto per il treno',
    description: 'Compra un biglietto Circumflegrea alla macchina EAV in stazione.',
    steps: ['Trova la macchinetta EAV', 'Acquista un biglietto (€ 2,20)'],
    reward: 0,
  },
  {
    id: 'pacco', title: 'Una consegna nel quartiere',
    description: 'Ritira il pacco da Donna Rosa e consegnalo al residente davanti alla stazione.',
    steps: ['Parla con Donna Rosa', 'Consegna il pacco al residente'],
    reward: 8,
  },
  {
    id: 'smarrito', title: 'Le chiavi smarrite',
    description: 'Trova le chiavi vicino al marciapiede e restituiscile all’anziano signore.',
    steps: ['Raccogli le chiavi', 'Restituiscile al signore'],
    reward: 5,
  },
  {
    id: 'lavoro', title: 'Una piccola mansione',
    description: 'Aiuta il barista: servi tre caffè ai clienti del bar.',
    steps: ['Accetta l’incarico al bar', 'Servi il primo caffè', 'Servi il secondo caffè', 'Servi il terzo caffè'],
    reward: 12,
  },
];

export class QuestSystem {
  states: QuestState[];

  constructor(save: SaveData) {
    this.states = QUEST_DEFS.map(def => {
      const found = save.quests.find(q => q.id === def.id);
      return found ? { ...found } : { id: def.id, progress: 0, done: false, accepted: false };
    });
  }

  get(id: string): QuestState | undefined { return this.states.find(q => q.id === id); }
  def(id: string): QuestDef | undefined { return QUEST_DEFS.find(q => q.id === id); }

  accept(id: string): void {
    const q = this.get(id);
    if (q && !q.accepted) { q.accepted = true; q.progress = 0; }
  }

  advance(id: string, amount = 1): boolean {
    const q = this.get(id);
    if (!q || q.done) return false;
    q.accepted = true;
    q.progress += amount;
    const def = this.def(id);
    if (def && q.progress >= def.steps.length) {
      q.done = true;
      return true; // completata ora
    }
    return false;
  }

  isDone(id: string): boolean { return !!this.get(id)?.done; }

  write(save: SaveData): void { save.quests = this.states.map(q => ({ ...q })); }
}
