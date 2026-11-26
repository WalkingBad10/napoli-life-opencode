import Phaser from 'phaser';
import './style.css';
import { BootScene } from './scenes/BootScene';
import { WorldScene } from './scenes/WorldScene';

// Il titolo deve scomparire immediatamente, anche prima che la scena finisca di caricare.
document.getElementById('start-btn')?.addEventListener('click', () => {
  document.getElementById('title')?.classList.add('hidden');
  document.getElementById('hud')?.classList.remove('hidden');
  document.getElementById('iconbar')?.classList.remove('hidden');
  document.getElementById('touch')?.classList.remove('hidden');
  (window as any).__napoliStarted = true;
  window.dispatchEvent(new Event('napoli-start'));
});

/** Un solo motore grafico (Phaser 3) e un solo renderer 2D Canvas, per compatibilità universale. */
new Phaser.Game({
  type: Phaser.CANVAS,
  parent: 'game',
  backgroundColor: '#20262c',
  pixelArt: true,
  roundPixels: true,
  antialias: false,
  scale: {
    mode: Phaser.Scale.RESIZE,
    autoCenter: Phaser.Scale.CENTER_BOTH,
    width: window.innerWidth,
    height: window.innerHeight,
  },
  input: {
    activePointers: 3,
    gamepad: true,
    keyboard: true,
    touch: { capture: true },
  },
  physics: {
    default: 'arcade',
    arcade: { debug: false },
  },
  render: {
    powerPreference: 'high-performance',
  },
  scene: [BootScene, WorldScene],
});
