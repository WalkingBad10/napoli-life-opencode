import Phaser from 'phaser';
import {
  AUTOSAVE_MS, BUILD_ID, BUSINESS_HOURS, HOME_FURNITURE, INTERACT_RADIUS_PX,
  JOB_DEFS, MENU, PPM, SECTOR_M, SPAWN, TRAIN_SPEED, VERSION,
} from '../config';
import { NPC, type NPCAnchors } from '../entities/NPC';
import { Player } from '../entities/Player';
import { createTraffic, type Vehicle } from '../entities/Traffic';
import { AudioSystem } from '../systems/AudioSystem';
import { BusinessSystem } from '../systems/BusinessSystem';
import { InputSystem } from '../systems/InputSystem';
import { JobSystem } from '../systems/JobSystem';
import { NeedsSystem } from '../systems/NeedsSystem';
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
  needs!: NeedsSystem;
  business!: BusinessSystem;
  jobs!: JobSystem;
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
  private hintText!: Phaser.GameObjects.Text;
  private nightOverlay!: Phaser.GameObjects.Rectangle;
  private windowLights!: Phaser.GameObjects.Graphics;
  private homeOverlay!: Phaser.GameObjects.Graphics;
  private fpsText!: Phaser.GameObjects.Text;
  private autosaveTimer = 0;
  private lightTimer = 0;
  private trainSoundTimer = 0;
  private room: string | null = null;
  private roomImage!: Phaser.GameObjects.Image;
  private roomPlayer!: Phaser.GameObjects.Sprite;
  private roomHint!: Phaser.GameObjects.Image;
  private lastWorldSpawn: [number, number] = [SPAWN.x, SPAWN.y];
  private lastPlayerPos: [number, number] = [SPAWN.x, SPAWN.y];
  private riding = false;
  private rideSpeed = 0;
  private paidJobs = new Set<string>();

  constructor() { super('World'); }

  create(): void {
    const data = this.registry.get('gameData') as GameData;
    this.world = data.world;
    this.buildings = data.buildings;
    this.interiors = data.interiors;

    this.save = SaveSystem.load();
    this.clock = new TimeSystem(this.save);
    this.quests = new QuestSystem(this.save);
    this.needs = new NeedsSystem(this.save);
    this.business = new BusinessSystem();
    this.jobs = new JobSystem(this.save);
    this.collision = new CollisionWorld(this.world);
    this.inputSystem = new InputSystem(this);
    this.audio2 = new AudioSystem(this);
    this.ui = new UI(this);
    this.ui.setWorld(this.world);

    this.cameras.main.setBackgroundColor('#b9b09c');
    this.setWorldCameraBounds();
    // 1 m = 16 px: zoom moderato per leggere facciate e dettagli senza perdere il contesto.
    this.cameras.main.setZoom(1.3);
    this.physics.world.setBounds(-PPM * 152, -PPM * 152, PPM * 304, PPM * 304);

    this.createGround();
    this.createBuildings();
    this.placeProps();
    this.createActors();
    this.createOverlays();

    this.player = new Player(this, this.save.player.x, this.save.player.y,
      this.save.player.appearance, this.collision, () => this.audio2.sfx('step', 0.12));
    this.lastPlayerPos = [this.player.mx, this.player.my];
    this.cameras.main.startFollow(this.player.sprite, true, 0.12, 0.12);

    this.roomImage = this.add.image(0, 0, 'room_station').setOrigin(0, 0).setVisible(false).setDepth(-10);
    this.roomPlayer = this.add.sprite(0, 0, this.save.player.appearance, 0).setOrigin(0.5, 30 / 32).setDepth(500).setVisible(false);
    this.drawHintTexture();
    this.hint = this.add.image(0, 0, 'hint').setVisible(false).setDepth(10000);
    this.roomHint = this.add.image(0, 0, 'hint').setVisible(false).setDepth(10001);
    this.hintText = this.add.text(0, 0, '', {
      fontFamily: 'monospace', fontSize: '12px', color: '#f4ebd6',
      backgroundColor: 'rgba(30,26,22,0.78)', padding: { x: 4, y: 2 },
    }).setOrigin(0.5, 0).setVisible(false).setDepth(10000).setScrollFactor(1);

    this.applyAudioSettings();
    this.applyHourNPCs(true);
    this.audio2.setZone(this.clock.phase, null, this.clock.populationFactor);
    this.updateHUD();

    // Hook di sola lettura per i test automatici (nessun indicatore visivo in gioco).
    (window as any).__napoli = {
      ready: true,
      version: VERSION,
      build: BUILD_ID,
      state: () => ({
        x: this.player.mx, y: this.player.my, room: this.room,
        money: this.save.money, inventory: { ...this.save.inventory },
        clock: this.clock.clock, version: VERSION,
        quests: this.quests.states.map(q => ({ ...q })),
        // Nuovi campi: solo aggiunte, i vecchi restano invariati.
        time: { minute: this.clock.minute, day: this.clock.day, absolute: this.clock.absoluteMinute },
        needs: { ...this.needs.state, status: this.needs.status },
        home: JSON.parse(JSON.stringify(this.save.home)),
        job: { ...this.jobs.state, label: this.jobs.label, progressText: this.jobs.progressText },
        train: { ...this.save.train, riding: this.riding, speed: this.rideSpeed,
                 x: this.train.position.x, y: this.train.position.y },
        open: this.openState(),
        stats: { ...this.save.stats },
        audio: this.audio2.state(),
      }),
      teleport: (x: number, y: number) => {
        this.player.mx = x; this.player.my = y;
        this.player.sprite.setPosition(x * PPM, y * PPM);
      },
      setTime: (minute: number, day?: number) => this.setTime(minute, day),
      setNeeds: (values: Partial<{ hunger: number; energy: number }>) => this.setNeeds(values),
      setMoney: (value: number) => { this.save.money = Math.max(0, Math.round(value * 100) / 100); this.updateHUD(); },
      teleportRoom: (x: number, y: number) => {
        if (this.room) { this.roomPlayer.setPosition(x, y); return true; }
        return false;
      },
      interact: (id: string) => this.debugInteract(id),
      boardTrain: () => this.boardTrain(),
      setTrain: (t: number) => { this.train.progress = t; },
      audioState: () => this.audio2.state(),
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

  private setWorldCameraBounds(): void {
    this.cameras.main.setBounds(-PPM * 152, -PPM * 152, PPM * 304, PPM * 304);
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
        // I settori sono generati direttamente a 16 px/m: nessuna scala applicata.
        const sprite = this.add.image(x * PPM, y * PPM, `sector_${x}_${y}`)
          .setOrigin(0, 0).setDepth(-1000);
        this.sectorSprites.push({ sprite, x, y });
      }
    }
  }

  private createBuildings(): void {
    for (const b of this.buildings) {
      // L'origine è il centro del bordo sud (livello strada), calcolata dal generatore.
      const sprite = this.add.image(b.anchor_x * PPM, b.anchor_y * PPM, `bld_${b.id.replace('/', '_')}`)
        .setOrigin(b.origin_x ?? 0.5, b.origin_y ?? 1)
        .setDepth(b.anchor_y * PPM + 1);
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
    // Macchinetta EAV sulla banchina, davanti all'ingresso reale del fabbricato.
    this.add.image(-3 * PPM, -4.6 * PPM, 'ticket_machine')
      .setOrigin(0.5, 0.95).setDepth(-4.6 * PPM + 1);
    // Veicoli parcheggiati: origine coerente con la metrica 1 m = 16 px.
    [[11, 18], [-31, 24], [42, -18], [-44, 8]].forEach(([x, y], i) => {
      this.add.image(x * PPM, y * PPM, i % 2 ? 'car_silver' : 'car_red')
        .setOrigin(0.5, 30 / 40).setRotation(0.04 * i).setDepth(y * PPM + 1);
    });
  }

  private createActors(): void {
    const traffic = createTraffic(this, this.world);
    this.vehicles = traffic.vehicles;
    this.train = traffic.train;

    const paths = this.world.roads.filter(r => r.name && r.points.length > 2 && r.points.some(([x, y]) => Math.abs(x) < 130 && Math.abs(y) < 130));
    const p = (i: number) => paths[i % Math.max(1, paths.length)].points.map(([x, y]) => ({ x, y }));
    const mk = (id: string, name: string, texture: string, x: number, y: number, pathIdx: number,
                morning: string[], afternoon: string[], evening: string[], anchors?: NPCAnchors) => {
      this.npcs.push(new NPC(this, id, name, texture, x, y, p(pathIdx),
        { morning, afternoon, evening }, this.collision, anchors));
    };
    mk('npc1', 'Antonio, il barista', 'vendor', -13.5, -54.5, 0,
      ['Buongiorno! Il caffè è appena fatto.', 'Oggi c’è il sole, si sta bene fuori.'],
      ['Un espresso? Lo preparo io.', 'La Circumflegrea è puntuale, oggi.'],
      ['A domani! Chiudiamo presto.'],
      { morning: { x: -16, y: -55 }, afternoon: { x: -13.5, y: -54.5 }, evening: { x: -19, y: -50 }, night: { x: -22, y: -44 }, activeFrom: 7, activeTo: 21 });
    mk('npc2', 'Rosa, la commerciante', 'resident', -15.6, -61.8, 1,
      ['Buongiorno, sono Rosa. Ho un pacco per te.', 'Vuoi qualcosa in negozio?'],
      ['Il pacco è qui, prendilo pure.', 'Pianura è un quartiere tranquillo.'],
      ['Buonasera, chiudo adesso.'],
      { morning: { x: 3, y: -59 }, afternoon: { x: -15.6, y: -61.8 }, evening: { x: -10, y: -54 }, night: { x: -2, y: -46 }, activeFrom: 8, activeTo: 20 });
    mk('npc3', 'Il signore con il cane', 'elderly', -20, 14, 2,
      ['Ho perso le chiavi… le avrai viste?', 'Il mio cane ama questa panchina.'],
      ['Le chiavi… ero qui vicino, credo.', 'Grazie per l’aiuto, giovane.'],
      ['Buonanotte a tutti.'],
      { morning: { x: -20, y: 14 }, afternoon: { x: -12, y: 9 }, evening: { x: -24, y: 16 }, night: { x: -27, y: 20 }, activeFrom: 8, activeTo: 21 });
    mk('npc4', 'Pendolare EAV', 'railway', 4, -3.6, 3,
      ['Il treno per Torregaveta arriva presto.', 'Biglietto preso?'],
      ['Ogni tanto prendo il treno per Montesanto.', 'La stazione è sempre affollata.'],
      ['Ultimo treno alle 21.'],
      { morning: { x: 2, y: -5 }, afternoon: { x: 26, y: -12 }, evening: { x: 0, y: -4 }, night: { x: 12, y: 4 }, activeFrom: 6, activeTo: 22 });
    mk('npc5', 'Maria, la vicina', 'resident', 3.5, 96, 4,
      ['Buongiorno! Sei nuovo del quartiere?', 'Le persiane qui si aprono presto.'],
      ['Porto la spesa a casa.', 'I panni stesi asciugano in fretta.'],
      ['Buonasera! A domani.'],
      { morning: { x: 6, y: 94 }, afternoon: { x: 18, y: 88 }, evening: { x: 3.5, y: 96 }, night: { x: 2, y: 100 }, activeFrom: 7, activeTo: 22 });
    mk('npc6', 'Lavoratore', 'worker', -35, -7, 5,
      ['Oggi c’è da lavorare al bar.', 'Che caldo fuori.'],
      ['Pausa pranzo, finalmente.', 'Passo davanti alla stazione ogni giorno.'],
      ['A casa, dopo una lunga giornata.'],
      { morning: { x: -35, y: -7 }, afternoon: { x: -22, y: -20 }, evening: { x: -8, y: -14 }, night: { x: -40, y: -4 }, activeFrom: 7, activeTo: 19 });
    mk('npc7', 'Ragazzo con lo scooter', 'teen', 24, -32, 6,
      ['Giro in scooter tutto il giorno.', 'Ciao!'],
      ['La piazza è il nostro posto.', 'Hai visto i miei amici?'],
      ['Ci vediamo domani.'],
      { morning: { x: 24, y: -32 }, afternoon: { x: 12, y: -25 }, evening: { x: 30, y: -38 }, night: { x: 34, y: -42 }, activeFrom: 9, activeTo: 22 });
    mk('npc8', 'Signora con la borsa', 'elderly', 8, 34, 7,
      ['Buongiorno, che bel tempo.', 'Vado a fare la spesa.'],
      ['Le scale qui sono ripide.', 'Il bar fa il miglior caffè.'],
      ['Buonanotte.'],
      { morning: { x: 8, y: 34 }, afternoon: { x: 20, y: 45 }, evening: { x: 5, y: 30 }, night: { x: 4, y: 38 }, activeFrom: 8, activeTo: 21 });

    // Le porte sono ancorate al bordo sud di edifici OSM reali, non al centro del fabbricato.
    this.interactables = [
      { id: 'station_door', label: 'Entra nella stazione', x: 0 * PPM, y: -6.1 * PPM, kind: 'interior:station' },
      { id: 'ticket', label: 'Macchinetta biglietti EAV', x: -3 * PPM, y: -4.6 * PPM, kind: 'ticket' },
      { id: 'bar_door', label: 'Entra al bar', x: -17 * PPM, y: -57.2 * PPM, kind: 'interior:bar' },
      { id: 'shop_door', label: 'Entra nel negozio', x: 3.7 * PPM, y: -60.1 * PPM, kind: 'interior:shop' },
      { id: 'home_door', label: 'Entra in casa', x: -0.75 * PPM, y: 100.2 * PPM, kind: 'interior:home' },
      // Carpe Diem: pizzeria OSM way/655446533, bbox [-132.87,111.84,-119.77,122.74].
      { id: 'pizzeria_door', label: 'Entra alla Pizzeria Carpe Diem', x: -126.3 * PPM, y: 123.9 * PPM, kind: 'interior:pizzeria' },
      { id: 'keys', label: 'Chiavi smarrite', x: -24 * PPM, y: 16 * PPM, kind: 'keys' },
      { id: 'job', label: 'Bacheca lavori', x: 25 * PPM, y: 20 * PPM, kind: 'job' },
      { id: 'train_board', label: 'Banchina Circumflegrea', x: 0 * PPM, y: -5 * PPM, kind: 'board' },
    ];
    // Oggetto della missione "chiavi smarrite", posizionato sul marciapiede.
    this.add.image(-24 * PPM, 16 * PPM, 'keys').setOrigin(0.5, 0.95).setDepth(16 * PPM + 1);
  }

  private createOverlays(): void {
    this.windowLights = this.add.graphics().setDepth(900).setScrollFactor(1);
    this.homeOverlay = this.add.graphics().setDepth(220).setScrollFactor(1);
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
    if (this.clock.update(delta)) this.minuteTick();

    if (this.riding) this.updateRide(dt);
    else if (this.room) this.updateRoom(dt);
    else this.updateWorld(dt);

    this.autosaveTimer += delta;
    if (this.autosaveTimer >= AUTOSAVE_MS) { this.autosaveTimer = 0; this.manualSave(); }
    this.ui.update(delta);
    this.updateHUD();
    this.updateLighting(delta);
    this.fpsText.setText(this.save.settings.showFps ? `${Math.round(1000 / Math.max(1, delta))} FPS` : '');
  }

  /** Un tick al minuto di gioco: bisogni, turni, routine e audio ambientale. */
  private minuteTick(): void {
    this.needs.update(this.clock.absoluteMinute, !this.riding);
    if (this.jobs.expire(this.clock.minute)) {
      const q = this.quests.get('lavoro');
      if (q) { q.accepted = false; q.progress = 0; q.done = false; }
      this.ui.toast('Il turno di lavoro è terminato');
    }
    this.clock.write(this.save);
    this.applyHourNPCs();
    this.audio2.setZone(this.clock.phase, this.room, this.clock.populationFactor);
  }

  private applyHourNPCs(force = false): void {
    for (const npc of this.npcs) npc.applyHour(this.clock.hour, force ? 0 : this.clock.minuteOfHour);
  }

  private setTime(minute: number, day?: number): void {
    this.clock.minute = ((Math.round(minute) % 1440) + 1440) % 1440;
    if (Number.isFinite(day)) this.clock.day = Math.max(1, Math.round(day!));
    this.needs.state.lastMinute = this.clock.absoluteMinute;
    this.clock.write(this.save);
    this.applyHourNPCs(true);
    this.audio2.setZone(this.clock.phase, this.room, this.clock.populationFactor);
    this.updateHUD();
  }

  private setNeeds(values: Partial<{ hunger: number; energy: number }>): void {
    if (Number.isFinite(values.hunger)) this.needs.state.hunger = Math.max(0, Math.min(100, values.hunger!));
    if (Number.isFinite(values.energy)) this.needs.state.energy = Math.max(0, Math.min(100, values.energy!));
    this.needs.state.lastMinute = this.clock.absoluteMinute;
    this.updateHUD();
  }

  private openState(): Record<string, boolean> {
    const out: Record<string, boolean> = {};
    for (const id of Object.keys(BUSINESS_HOURS)) out[id] = this.business.isOpen(id, this.clock.minute);
    return out;
  }

  private updateHUD(): void {
    this.ui.setHUD(this.clock.clock, this.save.money, this.needs.state, this.needs.status,
      this.save.home.owned, this.jobs.label, this.jobs.progressText);
  }

  private updateWorld(dt: number): void {
    const vec = this.inputSystem.getVector();
    const running = this.inputSystem.isRunning() && this.needs.state.energy > 12;
    this.player.update(dt, vec.x, vec.y, running);
    const stepDist = Math.hypot(this.player.mx - this.lastPlayerPos[0], this.player.my - this.lastPlayerPos[1]);
    if (stepDist > 0.001) this.save.stats.steps = Math.round((this.save.stats.steps + stepDist) * 10) / 10;
    this.lastPlayerPos = [this.player.mx, this.player.my];
    this.save.player.x = this.player.mx;
    this.save.player.y = this.player.my;

    const view = this.cameras.main.worldView;
    for (const s of this.sectorSprites) {
      s.sprite.setVisible(s.x * PPM < view.right && (s.x + SECTOR_M) * PPM > view.left &&
        s.y * PPM < view.bottom && (s.y + SECTOR_M) * PPM > view.top);
    }
    for (const b of this.buildingSprites) {
      // Sprite architettonici più alti: la soglia di culling deve coprire l'intera facciata.
      b.sprite.setVisible(b.y > view.top - 520 && b.y < view.bottom + 60);
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
    const showHint = !!nearest && !this.ui.isDialogOpen() && !this.ui.isPanelOpen();
    this.hint.setVisible(showHint);
    this.hintText.setVisible(showHint);
    if (nearest && showHint) {
      this.hint.setPosition(nearest.x, nearest.y - 52);
      this.hintText.setPosition(nearest.x, nearest.y - 70).setText(this.hintLabel(nearest));
    }

    if (this.inputSystem.consumeInteract() && nearest && !this.ui.isDialogOpen()) {
      this.handleInteract(nearest);
    }
    if (this.inputSystem.consumeCancel()) this.ui.closePanels();
  }

  private hintLabel(it: Interactable): string {
    if (it.kind.startsWith('interior:')) {
      const id = it.kind.split(':')[1];
      if (!this.business.isOpen(id, this.clock.minute)) {
        return `${this.business.label(id)} · chiuso (${this.business.hoursLabel(id)})`;
      }
    }
    if (it.id === 'train_board') {
      return this.canBoard() ? 'Sal a bordo del treno EAV' : 'Banchina Circumflegrea';
    }
    return it.label;
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
      this.windowLights.fillStyle(0xf3c765, 0.28 + darkness * 0.34);
      const wallW = b.width_px ?? b.w;
      // Il manifesto contiene le finestre vere costruite dal generatore: niente
      // griglia approssimata e nessuna luce su muri pieni o al piano terra.
      if (b.windows?.length) {
        b.windows.forEach(([cx, wy], i) => {
          if ((i + b.id.length) % 3 === 0) return;
          this.windowLights.fillRect(
            Math.round(x - wallW / 2 + cx - 4),
            Math.round(y + wy + 1), 8, 12);
        });
        continue;
      }
      // Compatibilità con manifest senza coordinate finestra (versioni precedenti).
      const wallH = b.wall_h_px ?? Math.max(46, Math.round(b.height_m / 2.85) * 46);
      const cols = Math.max(1, Math.floor((wallW - 24) / 38));
      const rows = Math.max(2, Math.floor(wallH / 46));
      for (let c = 0; c < cols; c++) {
        const px = x - wallW / 2 + 19 + c * 38;
        for (let row = 1; row < rows; row++) {
          if ((c + row + b.id.length) % 3 === 0) continue;
          this.windowLights.fillRect(px, y - 28 - row * 46, 8, 10);
        }
      }
    }
  }

  private updateRoom(dt: number): void {
    const vec = this.inputSystem.getVector();
    const speed = (this.inputSystem.isRunning() && this.needs.state.energy > 12) ? 130 : 78;
    let nx = this.roomPlayer.x + vec.x * speed * dt;
    let ny = this.roomPlayer.y + vec.y * speed * dt;
    nx = Phaser.Math.Clamp(nx, 16, 560);
    ny = Phaser.Math.Clamp(ny, 130, 360);
    const def = this.interiors[this.room!];
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
    const showHint = !!nearest && !this.ui.isDialogOpen();
    this.roomHint.setVisible(showHint);
    this.hintText.setVisible(showHint);
    if (nearest && showHint) {
      this.roomHint.setPosition(nearest.x, nearest.y - 30);
      this.hintText.setPosition(nearest.x, nearest.y - 50).setText(nearest.name);
    }
    if (this.inputSystem.consumeInteract() && nearest && !this.ui.isDialogOpen()) {
      this.handleRoomInteract(nearest);
    }
  }

  private canTrade(id: string): boolean {
    if (this.business.isOpen(id, this.clock.minute)) return true;
    this.ui.toast(this.business.closedMessage(id));
    return false;
  }

  private handleRoomInteract(it: InteriorDef['interactables'][number]): void {
    if (it.kind === 'exit') { this.exitRoom(); return; }
    if (it.kind === 'barista') {
      this.quests.accept('caffe');
      this.quests.advance('caffe');
      this.ui.showDialog('Barista', 'Buongiorno! Un espresso? Costa € 1,20. Ti va di aiutarmi oggi?', [
        { label: 'Un espresso, grazie', action: () => { if (this.canTrade('bar')) this.buyItem('caffe'); } },
        { label: 'Accetto il lavoretto', action: () => this.acceptJob('bar') },
        { label: 'Rimango a guardare', action: () => {} },
      ]);
      return;
    }
    if (it.kind === 'buy_food') {
      this.ui.showDialog('Vetrina', 'Dolci freschi, fatti qui. Vuoi acquistarne uno? (€ 2,00)', [
        { label: 'Compra (€ 2,00)', action: () => { if (this.canTrade(this.room ?? 'bar')) this.buyItem('dolce'); } },
        { label: 'No, grazie', action: () => {} },
      ]);
      return;
    }
    if (it.kind === 'shop') {
      this.ui.showDialog('Commerciante', 'Benvenuto! Posso venderti una bevanda o dell’acqua.', [
        { label: 'Bevanda (€ 1,50)', action: () => { if (this.canTrade('shop')) this.buyItem('bevanda'); } },
        { label: 'Acqua (€ 0,70)', action: () => { if (this.canTrade('shop')) this.buyItem('acqua'); } },
        { label: 'Parla del quartiere', action: () => this.ui.showDialog('Commerciante',
          'Qui vicino c’è la stazione Circumflegrea. Da qui si va a Torregaveta o a Montesanto.') },
      ]);
      return;
    }
    if (it.kind === 'ticket') {
      this.ui.showDialog('Addetto EAV', `Il biglietto per la Circumflegrea costa € 2,20. Stazione aperta ${this.business.hoursLabel('station')}.`, [
        { label: 'Compra il biglietto', action: () => { if (this.canTrade('station')) this.buyTicket(); } },
        { label: 'Guarda gli orari', action: () => this.showTimetable() },
      ]);
      return;
    }
    if (it.kind === 'read') {
      if (this.room === 'pizzeria') {
        this.ui.showDialog('Menu Carpe Diem', 'Pizza al taglio € 4,50 · Bevanda € 1,50 · Espresso € 1,20. Forno a legna, specialità napoletane.');
      } else this.showTimetable();
      return;
    }
    if (it.kind === 'pizzaiolo') {
      this.ui.showDialog('Pizzaiolo', 'Benvenuto alla Carpe Diem! Vuoi una pizza al taglio o dare una mano in forno?', [
        { label: 'Pizza al taglio (€ 4,50)', action: () => { if (this.canTrade('pizzeria')) this.buyItem('pizza'); } },
        { label: 'Aiuta in pizzeria', action: () => this.acceptJob('pizzeria') },
        { label: 'Leggi il menu', action: () => this.handleRoomInteract({ ...it, kind: 'read' }) },
      ]);
      return;
    }
    if (it.kind === 'buy_pizza') {
      this.ui.showDialog('Banco', 'Pizza al taglio appena sfornata — € 4,50.', [
        { label: 'Compra (€ 4,50)', action: () => { if (this.canTrade('pizzeria')) this.buyItem('pizza'); } },
        { label: 'No, grazie', action: () => {} },
      ]);
      return;
    }
    if (it.kind === 'furnish') {
      const f = this.save.home.furniture;
      const options = [];
      if (!f.bookshelf) options.push({ label: `Compra libreria (€ ${HOME_FURNITURE.bookshelf.price.toFixed(2)})`, action: () => this.buyFurniture('bookshelf') });
      if (!f.plant) options.push({ label: `Compra pianta (€ ${HOME_FURNITURE.plant.price.toFixed(2)})`, action: () => this.buyFurniture('plant') });
      options.push({ label: 'Chiudi', action: () => {} });
      this.ui.showDialog('Armadio', 'Puoi rendere la casa più tua con pochi acquisti. Arredi e salvataggio restano sul dispositivo.', options);
      return;
    }
    if (it.kind === 'sleep') {
      const minutes = this.save.home.owned ? 120 : 30;
      this.clock.advance(minutes);
      this.needs.afterSleep(minutes, this.clock.absoluteMinute);
      this.clock.write(this.save);
      this.applyHourNPCs(true);
      this.audio2.setZone(this.clock.phase, this.room, this.clock.populationFactor);
      this.audio2.sfx('sleep', 0.28);
      this.ui.toast(`Ti sei riposato fino alle ${this.clock.clock} · energia ${Math.round(this.needs.state.energy)}`);
      return;
    }
  }

  private showTimetable(): void {
    const h = this.clock.hour;
    const base = h < 6 ? 6 : h;
    const fmt = (m: number) => `${String((Math.floor(m / 60)) % 24).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;
    this.ui.showDialog('Tabellone EAV', `Partenze: ${fmt(base * 60 + 12)} Torregaveta · ${fmt(base * 60 + 40)} Napoli · ${fmt((base + 1) * 60 + 5)} Torregaveta. Stazione ${this.business.hoursLabel('station')}.`);
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
        this.ui.showDialog('Bacheca lavori', 'C’è lavoro al bar e in pizzeria. I turni durano fino a due ore.', [
          { label: 'Bar — servi 3 espressi (€ 12)', action: () => this.acceptJob('bar') },
          { label: 'Pizzeria — prepara 3 pizze (€ 18)', action: () => this.acceptJob('pizzeria') },
          { label: 'Guarda solo', action: () => {} },
        ]);
        break;
      case 'board':
        this.ui.showDialog('Banchina', 'Il treno EAV della Circumflegrea collega Pianura a Torregaveta e Montesanto.', [
          ...(this.canBoard() ? [{ label: 'Sal a bordo', action: () => this.boardTrain() }] : []),
          { label: 'Guarda il treno passare', action: () => this.audio2.sfx('train', 0.3) },
          { label: 'Orari EAV', action: () => this.showTimetable() },
          { label: 'Va bene', action: () => {} },
        ]);
        break;
    }
  }

  private talkToNPC(id: string): void {
    const npc = this.npcs.find(n => n.id === id);
    if (!npc) return;
    const text = npc.talk(this.clock.hour, this.clock.minuteOfHour);
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
    } else if (id === 'npc6') {
      this.ui.showDialog(npc.name, `${text} Se vuoi, la bacheca vicino alla stazione ha lavori per oggi.`);
    } else {
      this.ui.showDialog(npc.name, text);
    }
  }

  private acceptJob(id: string): void {
    if (this.jobs.state.active) {
      this.ui.showDialog('Lavoro', `Stai già facendo: ${this.jobs.label} (${this.jobs.progressText}).`);
      return;
    }
    if (!this.jobs.accept(id, this.clock.minute)) return;
    if (id === 'bar') {
      const q = this.quests.get('lavoro');
      if (q) { q.accepted = true; q.progress = 1; q.done = false; }
    }
    this.audio2.sfx('ui', 0.2);
    this.ui.toast(`Lavoro accettato: ${this.jobs.label} · ${this.jobs.progressText}`);
  }

  private contributeJob(id: string, item: string): void {
    const result = this.jobs.contribute(id, item);
    if (result === 'none') return;
    if (id === 'bar') {
      if (this.quests.advance('lavoro') && !this.paidJobs.has('bar')) {
        this.paidJobs.add('bar');
        this.save.flags.job_bar_paid = true;
        this.save.stats.jobs++;
        this.addMoney(JOB_DEFS.bar.pay);
        this.audio2.sfx('cash', 0.3);
        this.ui.toast(`Lavoro completato: + € ${JOB_DEFS.bar.pay.toFixed(2)}`);
      }
      return;
    }
    if (result === 'done' && !this.paidJobs.has(id)) {
      this.paidJobs.add(id);
      this.save.flags[`job_${id}_paid`] = true;
      this.save.stats.jobs++;
      this.addMoney(JOB_DEFS[id].pay);
      this.audio2.sfx('cash', 0.3);
      this.ui.toast(`Lavoro completato: + € ${JOB_DEFS[id].pay.toFixed(2)}`);
    }
  }

  private buyItem(id: string): boolean {
    const entry = MENU[id];
    if (!entry) return false;
    if (!this.spend(entry.price, id)) { this.ui.toast('Denaro insufficiente'); return false; }
    this.needs.eat(id);
    this.audio2.sfx('eat', 0.22);
    if (id === 'caffe') {
      this.save.stats.coffees++;
      this.quests.advance('caffe');
      this.contributeJob('bar', 'caffe');
    }
    if (id === 'pizza') {
      this.save.stats.pizzas++;
      this.contributeJob('pizzeria', 'pizza');
    }
    this.ui.toast(`${entry.name} acquistato · sazietà +${entry.hunger}`);
    return true;
  }

  private buyEspresso(): void { this.buyItem('caffe'); }

  /** Consumo dall'inventario: i cibi comprati NON spariscono dal gioco senza effetto. */
  consumeItem(id: string): boolean {
    const entry = MENU[id];
    if (!entry || !(this.save.inventory[id] ?? 0)) return false;
    this.save.inventory[id]--;
    if (this.save.inventory[id] <= 0) delete this.save.inventory[id];
    this.needs.eat(id);
    this.audio2.sfx('eat', 0.2);
    this.ui.toast(`${entry.name} consumato · sazietà +${entry.hunger}`);
    return true;
  }

  private buyTicket(): void {
    if (!this.spend(2.2, 'biglietto')) { this.ui.toast('Denaro insufficiente'); return; }
    this.save.stats.tickets++;
    this.save.train.ticketUntil = this.clock.absoluteMinute + 90;
    this.quests.accept('biglietto');
    this.quests.advance('biglietto');
    this.quests.advance('biglietto');
    this.audio2.sfx('coin', 0.3);
    this.ui.toast('Biglietto EAV acquistato — valido 90 minuti');
  }

  private buyFurniture(id: 'bookshelf' | 'plant'): void {
    const def = HOME_FURNITURE[id];
    if (this.save.home.furniture[id]) return;
    if (!this.spend(def.price, id)) { this.ui.toast('Denaro insufficiente'); return; }
    this.save.home.furniture[id] = true;
    this.audio2.sfx('cash', 0.25);
    this.drawHomeFurniture();
    this.ui.toast(`${def.name} acquistato e sistemato in casa`);
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

  private canBoard(): boolean {
    return (this.save.inventory.biglietto ?? 0) > 0 &&
      this.clock.absoluteMinute <= this.save.train.ticketUntil &&
      Math.abs(this.train.position.x) < 20;
  }

  private boardTrain(): void {
    if (!this.canBoard()) {
      this.ui.toast('Serve un biglietto EAV valido e il treno in banchina');
      return;
    }
    delete this.save.inventory.biglietto;
    this.save.train.ticketUntil = 0;
    this.riding = true;
    this.rideSpeed = 0;
    this.train.manual = true;
    this.train.velocity = 0;
    this.player.sprite.setVisible(false);
    this.hint.setVisible(false);
    this.hintText.setVisible(false);
    // Il percorso rail arriva oltre i ±150 m: la camera segue il treno senza tagliarlo.
    this.cameras.main.setBounds(-PPM * 230, -PPM * 152, PPM * 460, PPM * 304);
    this.cameras.main.startFollow(this.train.sprite, true, 0.08, 0.08);
    this.audio2.sfx('door', 0.25);
    this.ui.toast('A bordo del treno EAV — frecce per accelerare/frenare, E per scendere');
  }

  private updateRide(dt: number): void {
    const vec = this.inputSystem.getVector();
    this.rideSpeed = Phaser.Math.Clamp(this.rideSpeed + (vec.x * 5 - vec.y * 5) * dt, 0, TRAIN_SPEED);
    if (Math.abs(vec.x) < 0.05 && Math.abs(vec.y) < 0.05) this.rideSpeed = Math.max(0, this.rideSpeed - 0.9 * dt);
    this.train.velocity = this.rideSpeed;
    this.train.progress += (this.rideSpeed * dt) / Math.max(1, this.train.lengthMeters);
    this.train.update(dt, false);
    const p = this.train.position;
    this.player.mx = p.x;
    this.player.my = p.y + 0.2;
    this.save.player.x = this.player.mx;
    this.save.player.y = this.player.my;
    this.needs.update(this.clock.absoluteMinute, false);
    if (this.inputSystem.consumeInteract() && !this.ui.isDialogOpen()) {
      this.ui.showDialog('A bordo', `Treno EAV · ${this.rideSpeed.toFixed(1)} m/s. Vuoi scendere?`, [
        { label: 'Scendi a Pianura', action: () => this.disembark() },
        { label: 'Continua il viaggio', action: () => {} },
      ]);
    }
    if (this.inputSystem.consumeCancel()) this.ui.closePanels();
    this.hintText.setPosition(this.train.sprite.x, this.train.sprite.y - 44)
      .setText(`EAV ${this.rideSpeed.toFixed(1)} m/s · E per scendere`).setVisible(true);
    this.hint.setVisible(false);
  }

  private disembark(): void {
    this.riding = false;
    this.train.manual = false;
    this.train.velocity = TRAIN_SPEED;
    this.save.train.rides++;
    this.save.stats.rides++;
    this.player.mx = 0;
    this.player.my = -5.2;
    this.player.sprite.setPosition(this.player.mx * PPM, this.player.my * PPM);
    this.player.sprite.setVisible(true);
    this.lastPlayerPos = [this.player.mx, this.player.my];
    this.hintText.setVisible(false);
    this.setWorldCameraBounds();
    this.cameras.main.startFollow(this.player.sprite, true, 0.12, 0.12);
    this.audio2.sfx('door', 0.25);
    this.ui.toast('Sei sceso sulla banchina di Pianura');
  }

  private enterRoom(name: string): void {
    const def = this.interiors[name];
    if (!def) return;
    if (!this.business.isOpen(name, this.clock.minute)) {
      this.ui.toast(this.business.closedMessage(name));
      return;
    }
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
    this.audio2.setZone(this.clock.phase, name, this.clock.populationFactor);
    this.drawHomeFurniture();
    this.ui.toast(name === 'home' ? 'Sei in casa' : name === 'bar' ? 'Benvenuto al bar'
      : name === 'shop' ? 'Nel negozio' : name === 'pizzeria' ? 'Pizzeria Carpe Diem' : 'Stazione Circumflegrea');
  }

  private exitRoom(): void {
    const def = this.interiors[this.room!];
    this.room = null;
    this.roomImage.setVisible(false);
    this.roomPlayer.setVisible(false);
    this.roomHint.setVisible(false);
    this.hintText.setVisible(false);
    this.homeOverlay.clear();
    this.player.sprite.setVisible(true);
    this.player.mx = def.door.spawn[0];
    this.player.my = def.door.spawn[1];
    this.lastPlayerPos = [this.player.mx, this.player.my];
    this.player.sprite.setPosition(this.player.mx * PPM, this.player.my * PPM);
    this.cameras.main.setZoom(1.3);
    this.cameras.main.startFollow(this.player.sprite, true, 0.12, 0.12);
    this.audio2.sfx('door', 0.3);
    this.audio2.setZone(this.clock.phase, null, this.clock.populationFactor);
  }

  /** Arredi acquistati: disegnati sopra il PNG dell'intero, in coordinate 48 px/m. */
  private drawHomeFurniture(): void {
    this.homeOverlay.clear();
    if (this.room !== 'home') return;
    const f = this.save.home.furniture;
    if (f.bookshelf) {
      this.homeOverlay.fillStyle(0x6b4a2f, 1).fillRect(420, 118, 52, 64);
      this.homeOverlay.fillStyle(0x8a623a, 1).fillRect(424, 122, 44, 56);
      const colors = [0xa84638, 0x3f6d8c, 0xc0a247, 0x5e7c4a];
      for (let shelf = 0; shelf < 3; shelf++) {
        const y = 130 + shelf * 16;
        this.homeOverlay.fillStyle(0x4c3422, 1).fillRect(425, y + 13, 42, 3);
        for (let b = 0; b < 6; b++) {
          this.homeOverlay.fillStyle(colors[(b + shelf) % colors.length], 1);
          this.homeOverlay.fillRect(427 + b * 7, y + 2 + (b % 2) * 2, 5, 11 - (b % 2) * 2);
        }
      }
    }
    if (f.plant) {
      this.homeOverlay.fillStyle(0x9b5a3c, 1).fillRect(488, 142, 24, 22);
      this.homeOverlay.fillStyle(0xb26b48, 1).fillRect(486, 138, 28, 6);
      this.homeOverlay.fillStyle(0x3f7a45, 1);
      for (let i = 0; i < 6; i++) {
        const a = (i / 6) * Math.PI * 2;
        this.homeOverlay.fillCircle(500 + Math.cos(a) * 15, 126 + Math.sin(a) * 12, 8);
      }
      this.homeOverlay.fillStyle(0x5c9a51, 1).fillCircle(500, 122, 9);
    }
  }

  private debugInteract(id: string): boolean {
    if (this.room) {
      const it = this.interiors[this.room]?.interactables.find(x => x.id === id);
      if (!it) return false;
      this.handleRoomInteract(it);
      return true;
    }
    const it = this.interactables.find(x => x.id === id);
    if (!it) return false;
    this.handleInteract(it);
    return true;
  }

  // ---- API usate dalla UI HTML ----
  manualSave(): void {
    this.clock.write(this.save);
    this.quests.write(this.save);
    this.needs.write(this.save);
    this.jobs.write(this.save);
    this.business.write(this.save);
    for (const id of this.paidJobs) this.save.flags[`job_${id}_paid`] = true;
    if (this.save.player.appearance !== this.player.appearance) this.save.player.appearance = this.player.appearance;
    SaveSystem.save(this.save);
  }

  exportSave(): string { this.manualSave(); return SaveSystem.export(this.save); }

  importSave(text: string): boolean {
    const loaded = SaveSystem.import(text);
    if (!loaded) return false;
    this.rebindSave(loaded, true);
    this.ui.toast('Salvataggio importato');
    return true;
  }

  resetSave(): void {
    this.rebindSave(SaveSystem.reset(), true);
    this.ui.toast('Partita azzerata');
  }

  /** Reidrata tutti i sistemi dopo import/azzeramento, evitando Stato disallineato. */
  private rebindSave(loaded: SaveData, fromDialog: boolean): void {
    if (this.riding) this.disembark();
    this.room = null;
    this.roomImage.setVisible(false);
    this.roomPlayer.setVisible(false);
    this.roomHint.setVisible(false);
    this.homeOverlay.clear();
    this.hintText.setVisible(false);
    this.save = loaded;
    this.clock = new TimeSystem(loaded);
    this.quests = new QuestSystem(loaded);
    this.needs = new NeedsSystem(loaded);
    this.jobs = new JobSystem(loaded);
    this.paidJobs = new Set(Object.entries(loaded.flags)
      .filter(([k, v]) => k.startsWith('job_') && k.endsWith('_paid') && v)
      .map(([k]) => k.slice(4, -5)));
    this.player.mx = loaded.player.x;
    this.player.my = loaded.player.y;
    this.lastPlayerPos = [this.player.mx, this.player.my];
    this.player.sprite.setPosition(this.player.mx * PPM, this.player.my * PPM);
    this.player.sprite.setVisible(true);
    this.setAppearance(loaded.player.appearance);
    this.setWorldCameraBounds();
    this.cameras.main.setZoom(1.3);
    this.cameras.main.startFollow(this.player.sprite, true, 0.12, 0.12);
    this.applyHourNPCs(true);
    this.applyAudioSettings();
    this.audio2.setZone(this.clock.phase, null, this.clock.populationFactor);
    this.updateHUD();
    if (fromDialog) this.ui.hideDialog();
  }

  setAppearance(key: string): void { this.player.setAppearance(key); this.roomPlayer.setTexture(key); this.save.player.appearance = key; }
  applyAudioSettings(): void { this.audio2.apply(this.save.settings); }
}
