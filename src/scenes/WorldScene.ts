import Phaser from 'phaser';
import { AUTOSAVE_MS, INTERACT_RADIUS_PX, PPM, SECTOR_M, SPAWN, VERSION } from '../config';
import { NPC } from '../entities/NPC';
import { Player } from '../entities/Player';
import { createTraffic, type Vehicle } from '../entities/Traffic';
import { AudioSystem } from '../systems/AudioSystem';
import { InputSystem } from '../systems/InputSystem';
import { QuestSystem } from '../systems/QuestSystem';
import { SaveSystem } from '../systems/SaveSystem';
import { TimeSystem } from '../systems/TimeSystem';
import type { BuildingSprite, InteriorDef, Interactable, SaveData, WorldData } from '../types';
import { UI } from '../ui/UI';
import { CollisionWorld } from '../world/Collision';
import { WorldLoader } from '../world/WorldLoader';

type GameData = { world: WorldData; buildings: BuildingSprite[]; interiors: Record<string, InteriorDef> };

export class WorldScene extends Phaser.Scene {
  save!: SaveData;
  clock!: TimeSystem;
  quests!: QuestSystem;
  inputSystem!: InputSystem;
  ui!: UI;
  audio2!: AudioSystem;
  player!: Player;
  collision!: CollisionWorld;

  private world!: WorldData;
  private buildings!: BuildingSprite[];
  private interiors!: Record<string, InteriorDef>;
  private buildingSprites: { sprite: Phaser.GameObjects.Image; y: number }[] = [];
  private sectorSprites: { sprite: Phaser.GameObjects.Image; x: number; y: number }[] = [];
  private npcs: NPC[] = [];
  private vehicles: Vehicle[] = [];
  private train!: Vehicle;
  private interactables: Interactable[] = [];
  private hint!: Phaser.GameObjects.Image;
  private nightOverlay!: Phaser.GameObjects.Rectangle;
  private windowLights!: Phaser.GameObjects.Graphics;
  private fpsText!: Phaser.GameObjects.Text;
  private autosaveTimer = 0;
  private lightTimer = 0;
  private trainSoundTimer = 0;
  private room: string | null = null;
  private roomImage!: Phaser.GameObjects.Image;
  private roomPlayer!: Phaser.GameObjects.Sprite;
  private roomHint!: Phaser.GameObjects.Image;
  private lastWorldSpawn: [number, number] = [SPAWN.x, SPAWN.y];

  constructor() { super('World'); }

  create(): void {
    const data = this.registry.get('gameData') as GameData;
    this.world = data.world;
    this.buildings = data.buildings;
    this.interiors = data.interiors;

    this.save = SaveSystem.load();
    this.clock = new TimeSystem(this.save);
    this.quests = new QuestSystem(this.save);
    this.collision = new CollisionWorld(this.world);
    this.inputSystem = new InputSystem(this);
    this.audio2 = new AudioSystem(this);
    this.ui = new UI(this);
    this.ui.setWorld(this.world);

    this.cameras.main.setBackgroundColor('#b9b09c');
    this.cameras.main.setBounds(-PPM * 152, -PPM * 152, PPM * 304, PPM * 304);
    this.cameras.main.setZoom(1.15);
    this.physics.world.setBounds(-PPM * 152, -PPM * 152, PPM * 304, PPM * 304);

    this.createGround();
    this.createBuildings();
    this.placeProps();
    this.createActors();
    this.createOverlays();

    this.player = new Player(this, this.save.player.x, this.save.player.y,
      this.save.player.appearance, this.collision, () => this.audio2.sfx('step', 0.12));
    this.cameras.main.startFollow(this.player.sprite, true, 0.12, 0.12);

    this.roomImage = this.add.image(0, 0, 'room_station').setOrigin(0, 0).setVisible(false).setDepth(-10);
    this.roomPlayer = this.add.sprite(0, 0, this.save.player.appearance, 0).setOrigin(0.5, 0.94).setDepth(500).setVisible(false);
    this.drawHintTexture();
    this.hint = this.add.image(0, 0, 'hint').setVisible(false).setDepth(10000);
    this.roomHint = this.add.image(0, 0, 'hint').setVisible(false).setDepth(10001);

    this.applyAudioSettings();

    // Hook di sola lettura per i test automatici (nessun indicatore visivo in gioco).
    (window as any).__napoli = {
      ready: true,
      state: () => ({
        x: this.player.mx, y: this.player.my, room: this.room,
        money: this.save.money, inventory: { ...this.save.inventory },
        clock: this.clock.clock, version: VERSION,
        quests: this.quests.states.map(q => ({ ...q })),
      }),
      teleport: (x: number, y: number) => {
        this.player.mx = x; this.player.my = y;
        this.player.sprite.setPosition(x * PPM, y * PPM);
      },
      save: () => this.manualSave(),
    };

    this.scale.on('resize', (size: Phaser.Structs.Size) => {
      this.cameras.main.setSize(size.width, size.height);
      // La posizione del giocatore e i progressi non vengono toccati: nessun reload.
    });

    const welcome = () => this.ui.toast('Benvenuto a Pianura — Stazione Circumflegrea');
    window.addEventListener('napoli-start', welcome);
    if ((window as any).__napoliStarted) welcome();
  }

  private drawHintTexture(): void {
    if (this.textures.exists('hint')) return;
    const g = this.make.graphics({ x: 0, y: 0 });
    g.fillStyle(0x2b2622, 0.85);
    g.fillCircle(9, 9, 8);
    g.lineStyle(2, 0xf4ebd6, 1);
    g.strokeCircle(9, 9, 8);
    g.generateTexture('hint', 18, 18);
    g.destroy();
  }

  private createGround(): void {
    for (const x of [-192, -128, -64, 0, 64, 128]) {
      for (const y of [-192, -128, -64, 0, 64, 128]) {
        const sprite = this.add.image(x * PPM, y * PPM, `sector_${x}_${y}`)
          .setOrigin(0, 0).setScale(2).setDepth(-1000);
        this.sectorSprites.push({ sprite, x, y });
      }
    }
  }

  private createBuildings(): void {
    for (const b of this.buildings) {
      const sprite = this.add.image(b.anchor_x * PPM, b.anchor_y * PPM, `bld_${b.id.replace('/', '_')}`)
        .setOrigin(0.5, 1).setDepth(b.anchor_y * PPM);
      this.buildingSprites.push({ sprite, y: b.anchor_y * PPM });
    }
  }

  /** Arredi urbani posizionati sui marciapiedi reali, mai dentro edifici o sul sedime. */
  private placeProps(): void {
    let index = 0;
    for (const road of this.world.roads) {
      if (!['residential', 'tertiary', 'secondary', 'unclassified', 'service'].includes(road.kind)) continue;
      const pts = road.points;
      for (let i = 0; i < pts.length - 1; i++) {
        const [ax, ay] = pts[i], [bx, by] = pts[i + 1];
        const len = Math.hypot(bx - ax, by - ay);
        if (len < 6) continue;
        const ux = (bx - ax) / len, uy = (by - ay) / len;
        const nx = -uy, ny = ux;
        for (let d = 8; d < len - 4; d += 24) {
          const side = (index % 2) ? 1 : -1;
          const x = ax + ux * d + nx * 3.4 * side;
          const y = ay + uy * d + ny * 3.4 * side;
          if (Math.abs(x) > 148 || Math.abs(y) > 148 || this.collision.blocked(x, y, 0.6)) continue;
          let texture = 'lamp';
          if (index % 7 === 3) texture = 'bin';
          else if (index % 11 === 5) texture = 'tree';
          else if (index % 13 === 8) texture = 'planter';
          else if (index % 17 === 12) texture = 'bench';
          else if (index % 19 === 14) texture = 'sign';
          const sprite = this.add.image(x * PPM, y * PPM, texture)
            .setOrigin(0.5, 0.95).setDepth(y * PPM + 0.5);
          if (texture === 'lamp') sprite.setAlpha(0.98);
          index++;
        }
      }
    }
    // Props ancorati ai POI OSM reali
    for (const poi of this.world.pois) {
      if (poi.amenity === 'recycling' || poi.shop === 'convenience') {
        this.add.image(poi.x * PPM, poi.y * PPM, 'bin').setOrigin(0.5, 0.95).setDepth(poi.y * PPM + 1);
      }
    }
    // Veicoli parcheggiati
    [[11, 18], [-31, 24], [42, -18], [-44, 8]].forEach(([x, y], i) => {
      this.add.image(x * PPM, y * PPM, i % 2 ? 'car_silver' : 'car_red')
        .setOrigin(0.5, 0.75).setRotation(0.04 * i).setDepth(y * PPM + 1);
    });
  }

  private createActors(): void {
    const traffic = createTraffic(this, this.world);
    this.vehicles = traffic.vehicles;
    this.train = traffic.train;

    const paths = this.world.roads.filter(r => r.name && r.points.length > 2 && r.points.some(([x, y]) => Math.abs(x) < 130 && Math.abs(y) < 130));
    const p = (i: number) => paths[i % Math.max(1, paths.length)].points.map(([x, y]) => ({ x, y }));
    const mk = (id: string, name: string, texture: string, x: number, y: number, pathIdx: number,
                morning: string[], afternoon: string[], evening: string[]) => {
      this.npcs.push(new NPC(this, id, name, texture, x, y, p(pathIdx),
        { morning, afternoon, evening }, this.collision));
    };
    mk('npc1', 'Antonio, il barista', 'vendor', 17, -13, 0,
      ['Buongiorno! Il caffè è appena fatto.', 'Oggi c’è il sole, si sta bene fuori.'],
      ['Un espresso? Lo preparo io.', 'La Circumflegrea è puntuale, oggi.'],
      ['A domani! Chiudiamo presto.']);
    mk('npc2', 'Rosa, la commerciante', 'resident', -15.6, -61.8, 1,
      ['Buongiorno, sono Rosa. Ho un pacco per te.', 'Vuoi qualcosa in negozio?'],
      ['Il pacco è qui, prendilo pure.', 'Pianura è un quartiere tranquillo.'],
      ['Buonasera, chiudo adesso.']);
    mk('npc3', 'Il signore con il cane', 'elderly', -20, 14, 2,
      ['Ho perso le chiavi… le avrai viste?', 'Il mio cane ama questa panchina.'],
      ['Le chiavi… ero qui vicino, credo.', 'Grazie per l’aiuto, giovane.'],
      ['Buonanotte a tutti.']);
    mk('npc4', 'Pendolare EAV', 'railway', 4, -9, 3,
      ['Il treno per Torregaveta arriva presto.', 'Biglietto preso?'],
      ['Ogni tanto prendo il treno per Montesanto.', 'La stazione è sempre affollata.'],
      ['Ultimo treno alle 21.']);
    mk('npc5', 'Maria, la vicina', 'resident', 30, 20, 4,
      ['Buongiorno! Sei nuovo del quartiere?', 'Le persiane qui si aprono presto.'],
      ['Porto la spesa a casa.', 'I panni stesi asciugano in fretta.'],
      ['Buonasera! A domani.']);
    mk('npc6', 'Lavoratore', 'worker', -35, -7, 5,
      ['Oggi c’è da lavorare al bar.', 'Che caldo fuori.'],
      ['Pausa pranzo, finalmente.', 'Passo davanti alla stazione ogni giorno.'],
      ['A casa, dopo una lunga giornata.']);
    mk('npc7', 'Ragazzo con lo scooter', 'teen', 24, -32, 6,
      ['Giro in scooter tutto il giorno.', 'Ciao!'],
      ['La piazza è il nostro posto.', 'Hai visto i miei amici?'],
      ['Ci vediamo domani.']);
    mk('npc8', 'Signora con la borsa', 'elderly', 8, 34, 7,
      ['Buongiorno, che bel tempo.', 'Vado a fare la spesa.'],
      ['Le scale qui sono ripide.', 'Il bar fa il miglior caffè.'],
      ['Buonanotte.']);

    this.interactables = [
      { id: 'station_door', label: 'Entra nella stazione', x: 0 * PPM, y: -23 * PPM, kind: 'interior:station' },
      { id: 'ticket', label: 'Macchinetta biglietti EAV', x: -3 * PPM, y: -8 * PPM, kind: 'ticket' },
      { id: 'bar_door', label: 'Entra al bar', x: 17 * PPM, y: -13 * PPM, kind: 'interior:bar' },
      { id: 'shop_door', label: 'Entra nel negozio', x: 34 * PPM, y: -11 * PPM, kind: 'interior:shop' },
      { id: 'home_door', label: 'Entra in casa', x: -6 * PPM, y: 22 * PPM, kind: 'interior:home' },
      { id: 'keys', label: 'Chiavi smarrite', x: -24 * PPM, y: 16 * PPM, kind: 'keys' },
      { id: 'job', label: 'Bacheca lavori', x: 25 * PPM, y: 20 * PPM, kind: 'job' },
      { id: 'train_board', label: 'Banchina Circumflegrea', x: 0 * PPM, y: -5 * PPM, kind: 'board' },
    ];
    // Oggetto della missione "chiavi smarrite", posizionato sul marciapiede.
    this.add.image(-24 * PPM, 16 * PPM, 'keys').setOrigin(0.5, 0.95).setDepth(16 * PPM + 1);
  }

  private createOverlays(): void {
    this.windowLights = this.add.graphics().setDepth(900).setScrollFactor(1);
    this.nightOverlay = this.add.rectangle(0, 0, this.scale.width, this.scale.height, 0x35456a, 0)
      .setOrigin(0, 0).setScrollFactor(0).setDepth(950);
    this.nightOverlay.setBlendMode(Phaser.BlendModes.MULTIPLY);
    this.fpsText = this.add.text(12, 34, '', { fontFamily: 'monospace', fontSize: '11px', color: '#ffffff' })
      .setScrollFactor(0).setDepth(1000);
    this.scale.on('resize', (size: Phaser.Structs.Size) => {
      this.nightOverlay.setSize(size.width, size.height);
    });
  }

  update(_time: number, delta: number): void {
    const dt = Math.min(delta, 50) / 1000;
    if (this.clock.update(delta)) this.ui.setHUD(this.clock.clock, this.save.money);

    if (this.room) this.updateRoom(dt);
    else this.updateWorld(dt);

    this.autosaveTimer += delta;
    if (this.autosaveTimer >= AUTOSAVE_MS) { this.autosaveTimer = 0; this.manualSave(); }
    this.ui.update(delta);
    this.updateLighting(delta);
    this.ui.setHUD(this.clock.clock, this.save.money);
  }

  private updateWorld(dt: number): void {
    const vec = this.inputSystem.getVector();
    const running = this.inputSystem.isRunning();
    this.player.update(dt, vec.x, vec.y, running);
    this.save.player.x = this.player.mx;
    this.save.player.y = this.player.my;

    const view = this.cameras.main.worldView;
    for (const s of this.sectorSprites) {
      s.sprite.setVisible(s.x * PPM < view.right && (s.x + SECTOR_M) * PPM > view.left &&
        s.y * PPM < view.bottom && (s.y + SECTOR_M) * PPM > view.top);
    }
    for (const b of this.buildingSprites) {
      b.sprite.setVisible(b.y > view.top - 260 && b.y < view.bottom + 60);
    }

    for (const npc of this.npcs) {
      npc.update(dt, this.player.mx, this.player.my, this.clock.populationFactor > 0.3, this.clock.hour);
    }
    for (const v of this.vehicles) v.update(dt, this.clock.populationFactor > 0.25);
    this.train.update(dt, true);
    this.trainSoundTimer -= dt;
    if (this.trainSoundTimer <= 0 && Math.abs(this.train.sprite.x - this.player.sprite.x) < 600) {
      this.audio2.sfx('train', 0.18);
      this.trainSoundTimer = 22;
    }

    let nearest: Interactable | null = null;
    let nearestDist = INTERACT_RADIUS_PX;
    for (const it of this.interactables) {
      const d = Math.hypot(it.x - this.player.sprite.x, it.y - this.player.sprite.y);
      if (d < nearestDist) { nearest = it; nearestDist = d; }
    }
    for (const npc of this.npcs) {
      const d = Math.hypot(npc.sprite.x - this.player.sprite.x, npc.sprite.y - this.player.sprite.y);
      if (d < nearestDist) {
        nearest = { id: npc.id, label: `Parla con ${npc.name}`, x: npc.sprite.x, y: npc.sprite.y, kind: `npc:${npc.id}` };
        nearestDist = d;
      }
    }
    if (nearest && !this.ui.isDialogOpen() && !this.ui.isPanelOpen()) {
      this.hint.setPosition(nearest.x, nearest.y - 52).setVisible(true);
    } else {
      this.hint.setVisible(false);
    }

    if (this.inputSystem.consumeInteract() && nearest && !this.ui.isDialogOpen()) {
      this.handleInteract(nearest);
    }
    if (this.inputSystem.consumeCancel()) this.ui.closePanels();
  }

  private updateLighting(delta: number): void {
    const darkness = this.clock.darkness;
    this.nightOverlay.setAlpha(darkness * 0.62);
    this.lightTimer -= delta;
    if (this.lightTimer > 0) return;
    this.lightTimer = 2500;
    this.windowLights.clear();
    if (darkness < 0.22) return;
    const view = this.cameras.main.worldView;
    for (const b of this.buildings) {
      const x = b.anchor_x * PPM, y = b.anchor_y * PPM;
      if (x < view.left - 100 || x > view.right + 100 || y < view.top - 200 || y > view.bottom + 100) continue;
      this.windowLights.fillStyle(0xf3c765, 0.35 + darkness * 0.4);
      const cols = Math.max(1, Math.floor(b.w / 40));
      for (let c = 0; c < cols; c++) {
        const px = x - b.w / 2 + 20 + c * 40;
        for (let row = 0; row < Math.max(1, Math.round(b.height_m / 2.85)); row++) {
          if ((c + row + b.id.length) % 3 === 0) continue;
          this.windowLights.fillRect(px, y - 20 - row * 46, 6, 8);
        }
      }
    }
  }

  private updateRoom(dt: number): void {
    const vec = this.inputSystem.getVector();
    const speed = this.inputSystem.isRunning() ? 130 : 78;
    let nx = this.roomPlayer.x + vec.x * speed * dt;
    let ny = this.roomPlayer.y + vec.y * speed * dt;
    nx = Phaser.Math.Clamp(nx, 16, 560);
    ny = Phaser.Math.Clamp(ny, 130, 360);
    const def = this.interiors[this.room];
    const blocked = (x: number, y: number) => def.colliders.some(([x0, y0, x1, y1]) =>
      x > x0 - 8 && x < x1 + 8 && y > y0 - 8 && y < y1 + 8);
    if (!blocked(nx, this.roomPlayer.y)) this.roomPlayer.x = nx;
    if (!blocked(this.roomPlayer.x, ny)) this.roomPlayer.y = ny;
    if (Math.abs(vec.x) > 0.05 || Math.abs(vec.y) > 0.05) {
      const dir = Math.abs(vec.x) > Math.abs(vec.y) ? (vec.x > 0 ? 2 : 1) : (vec.y > 0 ? 0 : 3);
      this.roomPlayer.setFrame(dir * 4 + (Math.floor(this.clock.minute / 3) % 3) + 1);
    }
    this.roomPlayer.setDepth(this.roomPlayer.y);

    let nearest: InteriorDef['interactables'][number] | null = null;
    let best = 72;
    for (const it of def.interactables) {
      const d = Math.hypot(it.x - this.roomPlayer.x, it.y - this.roomPlayer.y);
      if (d < best) { best = d; nearest = it; }
    }
    if (nearest && !this.ui.isDialogOpen()) {
      this.roomHint.setPosition(nearest.x, nearest.y - 30).setVisible(true);
    } else this.roomHint.setVisible(false);

    if (this.inputSystem.consumeInteract() && nearest && !this.ui.isDialogOpen()) {
      this.handleRoomInteract(nearest);
    }
  }

  private handleRoomInteract(it: InteriorDef['interactables'][number]): void {
    if (it.kind === 'exit') { this.exitRoom(); return; }
    if (it.kind === 'barista') {
      this.quests.accept('caffe');
      this.quests.advance('caffe');
      this.ui.showDialog('Barista', 'Buongiorno! Un espresso? Costa € 1,20. Ti va di aiutarmi oggi?', [
        { label: 'Un espresso, grazie', action: () => this.buyEspresso() },
        { label: 'Accetto il lavoretto', action: () => this.acceptJob() },
        { label: 'Rimango a guardare', action: () => {} },
      ]);
      return;
    }
    if (it.kind === 'buy_food') {
      this.ui.showDialog('Vetrina', 'Dolci freschi, fatti qui. Vuoi acquistarne uno? (€ 2,00)', [
        { label: 'Compra (€ 2,00)', action: () => {
          if (this.spend(2, 'dolce')) this.ui.toast('Hai comprato un dolce');
          else this.ui.toast('Denaro insufficiente');
        } },
        { label: 'No, grazie', action: () => {} },
      ]);
      return;
    }
    if (it.kind === 'shop') {
      this.ui.showDialog('Commerciante', 'Benvenuto! Posso venderti un biglietto o una bevanda.', [
        { label: 'Bevanda (€ 1,50)', action: () => {
          if (this.spend(1.5, 'dolce')) this.ui.toast('Acquisto effettuato');
          else this.ui.toast('Denaro insufficiente');
        } },
        { label: 'Parla del quartiere', action: () => this.ui.showDialog('Commerciante',
          'Qui vicino c’è la stazione Circumflegrea. Da qui si va a Torregaveta o a Montesanto.') },
      ]);
      return;
    }
    if (it.kind === 'ticket') {
      this.ui.showDialog('Addetto EAV', 'Il biglietto per la Circumflegrea costa € 2,20.', [
        { label: 'Compra il biglietto', action: () => this.buyTicket() },
        { label: 'Guarda gli orari', action: () => this.ui.showDialog('Tabellone', 'Prossimi treni: 06:12 Torregaveta · 06:40 Napoli · 07:05 Torregaveta.') },
      ]);
      return;
    }
    if (it.kind === 'sleep') {
      this.clock.minute = (this.clock.minute + 120) % 1440;
      this.ui.toast('Ti sei riposato un po’');
      return;
    }
    if (it.kind === 'read') {
      this.ui.showDialog('Tabellone', 'Partenze: 06:12 Torregaveta · 06:40 Napoli · 07:05 Torregaveta.');
    }
  }

  private handleInteract(it: Interactable): void {
    if (it.kind.startsWith('interior:')) { this.enterRoom(it.kind.split(':')[1]); return; }
    if (it.kind.startsWith('npc:')) { this.talkToNPC(it.id); return; }
    switch (it.kind) {
      case 'ticket':
        this.ui.showDialog('Macchinetta EAV', 'Biglietto Circumflegrea — € 2,20. Valido 90 minuti.', [
          { label: 'Acquista', action: () => this.buyTicket() },
          { label: 'Annulla', action: () => {} },
        ]);
        break;
      case 'keys':
        if (this.save.inventory.chiavi) { this.ui.toast('Hai già raccolto le chiavi'); break; }
        this.save.inventory.chiavi = 1;
        this.quests.accept('smarrito');
        this.quests.advance('smarrito');
        this.children.list.forEach((obj: any) => {
          if (obj instanceof Phaser.GameObjects.Image && obj.texture?.key === 'keys' &&
              Math.hypot(obj.x - it.x, obj.y - it.y) < 2) obj.destroy();
        });
        this.ui.toast('Hai raccolto le chiavi smarrite');
        break;
      case 'job':
        this.acceptJob();
        break;
      case 'board':
        this.ui.showDialog('Banchina', 'Il treno EAV della Circumflegrea collega Pianura a Torregaveta e Montesanto.', [
          { label: 'Guarda il treno passare', action: () => this.audio2.sfx('train', 0.3) },
          { label: 'Va bene', action: () => {} },
        ]);
        break;
    }
  }

  private talkToNPC(id: string): void {
    const npc = this.npcs.find(n => n.id === id);
    if (!npc) return;
    const text = npc.talk(this.clock.hour);
    if (id === 'npc2' && !this.quests.get('pacco')?.accepted) {
      this.ui.showDialog('Rosa', `${text} Ho un pacco da consegnare a Maria, che abita poco più in là.`, [
        { label: 'Prendo il pacco', action: () => {
          this.save.inventory.pacco = 1;
          this.quests.accept('pacco');
          this.quests.advance('pacco');
          this.ui.toast('Hai ricevuto il pacco');
        } },
        { label: 'Dopo', action: () => {} },
      ]);
    } else if (id === 'npc5' && this.save.inventory.pacco && !this.quests.isDone('pacco')) {
      this.ui.showDialog('Maria', 'Oh, il pacco! Era tanto che lo aspettavo. Grazie!', [
        { label: 'Consegna il pacco', action: () => {
          delete this.save.inventory.pacco;
          this.quests.advance('pacco');
          this.addMoney(8);
          this.ui.toast('Missione completata: + € 8,00');
        } },
      ]);
    } else if (id === 'npc3' && this.save.inventory.chiavi && !this.quests.isDone('smarrito')) {
      this.ui.showDialog('Signore con il cane', 'Sono le mie chiavi! Dove le hai trovate? Grazie mille, prendi questa ricompensa.', [
        { label: 'Restituisci le chiavi', action: () => {
          delete this.save.inventory.chiavi;
          this.quests.advance('smarrito');
          this.addMoney(5);
          this.ui.toast('Missione completata: + € 5,00');
        } },
      ]);
    } else {
      this.ui.showDialog(npc.name, text);
    }
  }

  private acceptJob(): void {
    const q = this.quests.get('lavoro');
    if (q?.accepted) { this.ui.showDialog('Barista', 'Ricordati: servi tre caffè ai clienti!'); return; }
    this.quests.accept('lavoro');
    this.quests.advance('lavoro');
    this.ui.toast('Lavoro accettato: servi 3 caffè');
  }

  private buyEspresso(): void {
    if (!this.spend(1.2, 'caffe')) { this.ui.toast('Denaro insufficiente'); return; }
    this.save.stats.coffees++;
    this.quests.advance('caffe');
    if (this.quests.get('lavoro')?.accepted && !this.quests.isDone('lavoro')) {
      this.quests.advance('lavoro');
      if (this.quests.isDone('lavoro')) { this.addMoney(12); this.ui.toast('Lavoro completato: + € 12,00'); }
    }
    this.ui.toast('Espresso acquistato — buono!');
  }

  private buyTicket(): void {
    if (!this.spend(2.2, 'biglietto')) { this.ui.toast('Denaro insufficiente'); return; }
    this.save.stats.tickets++;
    this.quests.accept('biglietto');
    this.quests.advance('biglietto');
    this.quests.advance('biglietto');
    this.audio2.sfx('coin', 0.3);
    this.ui.toast('Biglietto EAV acquistato');
  }

  private spend(amount: number, item: string): boolean {
    if (this.save.money < amount) return false;
    this.save.money = Math.round((this.save.money - amount) * 100) / 100;
    this.save.inventory[item] = (this.save.inventory[item] ?? 0) + 1;
    return true;
  }

  private addMoney(amount: number): void {
    this.save.money = Math.round((this.save.money + amount) * 100) / 100;
    this.audio2.sfx('coin', 0.35);
  }

  private enterRoom(name: string): void {
    const def = this.interiors[name];
    if (!def) return;
    this.room = name;
    this.lastWorldSpawn = [this.player.mx, this.player.my];
    this.player.sprite.setVisible(false);
    this.hint.setVisible(false);
    this.roomImage.setTexture(`room_${name}`).setVisible(true).setPosition(0, 0);
    this.roomPlayer.setTexture(this.save.player.appearance).setPosition(def.door.x, def.door.y - 40).setVisible(true);
    this.cameras.main.stopFollow();
    this.cameras.main.setZoom(1.35);
    this.cameras.main.centerOn(288, 192);
    this.audio2.sfx('door', 0.3);
    this.ui.toast(name === 'home' ? 'Sei in casa' : name === 'bar' ? 'Benvenuto al bar' : name === 'shop' ? 'Nel negozio' : 'Stazione Circumflegrea');
  }

  private exitRoom(): void {
    const def = this.interiors[this.room!];
    this.room = null;
    this.roomImage.setVisible(false);
    this.roomPlayer.setVisible(false);
    this.roomHint.setVisible(false);
    this.player.sprite.setVisible(true);
    this.player.mx = def.door.spawn[0];
    this.player.my = def.door.spawn[1];
    this.player.sprite.setPosition(this.player.mx * PPM, this.player.my * PPM);
    this.cameras.main.setZoom(1.15);
    this.cameras.main.startFollow(this.player.sprite, true, 0.12, 0.12);
    this.audio2.sfx('door', 0.3);
  }

  // ---- API usate dalla UI HTML ----
  manualSave(): void {
    this.clock.write(this.save);
    this.quests.write(this.save);
    this.save.player.appearance = this.player.appearance;
    SaveSystem.save(this.save);
  }

  exportSave(): string { this.manualSave(); return SaveSystem.export(this.save); }
  importSave(text: string): boolean {
    const loaded = SaveSystem.import(text);
    if (!loaded) return false;
    this.save = loaded;
    this.clock = new TimeSystem(loaded);
    this.quests = new QuestSystem(loaded);
    this.player.mx = loaded.player.x; this.player.my = loaded.player.y;
    this.setAppearance(loaded.player.appearance);
    this.applyAudioSettings();
    return true;
  }
  resetSave(): void { this.save = SaveSystem.reset(); this.ui.toast('Partita azzerata'); }
  setAppearance(key: string): void { this.player.setAppearance(key); this.roomPlayer.setTexture(key); this.save.player.appearance = key; }
  applyAudioSettings(): void { this.audio2.apply(this.save.settings); }
}
