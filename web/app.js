const canvas = document.getElementById('world');
const ctx = canvas.getContext('2d');
const statsEl = document.getElementById('stats');

const W = 1024;
const H = 640;
const NX = 96;
const NY = 60;
const CELL_W = W / NX;
const CELL_H = H / NY;

let running = true;
let tick = 0;

function wrap(v, max) {
  return ((v % max) + max) % max;
}
function torusDelta(a, b, max) {
  let d = b - a;
  if (d > max / 2) d -= max;
  if (d < -max / 2) d += max;
  return d;
}
function torusDist(a, b) {
  const dx = torusDelta(a.x, b.x, W);
  const dy = torusDelta(a.y, b.y, H);
  return Math.hypot(dx, dy);
}

const elev = Array.from({ length: NX }, () => Array.from({ length: NY }, () => Math.random()));
for (let p = 0; p < 4; p++) {
  const next = Array.from({ length: NX }, () => Array.from({ length: NY }, () => 0));
  for (let i = 0; i < NX; i++) {
    for (let j = 0; j < NY; j++) {
      const ip = (i + 1) % NX, im = (i - 1 + NX) % NX;
      const jp = (j + 1) % NY, jm = (j - 1 + NY) % NY;
      next[i][j] = (elev[i][j] + elev[ip][j] + elev[im][j] + elev[i][jp] + elev[i][jm]) / 5;
    }
  }
  for (let i = 0; i < NX; i++) for (let j = 0; j < NY; j++) elev[i][j] = next[i][j];
}

const P = Array.from({ length: NX }, (_, i) => Array.from({ length: NY }, (_, j) => {
  const p = 1 - 3 * (elev[i][j] - 0.5) ** 2;
  return Math.max(0, Math.min(1, p));
}));
const K = Array.from({ length: NX }, (_, i) => Array.from({ length: NY }, (_, j) => 10 * P[i][j] + 0.2));
const N = Array.from({ length: NX }, (_, i) => Array.from({ length: NY }, (_, j) => 0.6 * K[i][j]));

function makeCreature(species) {
  return {
    species,
    sex: Math.random() < 0.5 ? 'F' : 'M',
    x: Math.random() * W,
    y: Math.random() * H,
    vx: 0,
    vy: 0,
    energy: species === 'H' ? 10 : 12,
    hp: species === 'H' ? 20 : 28,
    cooldown: 0,
    age: 0,
    speed: 1.0 + Math.random() * 2.0,
    vision: 20 + Math.random() * 60,
    attack: species === 'C' ? 2 + Math.random() * 5 : 0,
    size: 0.8 + Math.random() * 1.0,
  };
}

let creatures = [
  ...Array.from({ length: 160 }, () => makeCreature('H')),
  ...Array.from({ length: 45 }, () => makeCreature('C')),
];

function cellOf(c) {
  return [Math.floor(c.x / W * NX) % NX, Math.floor(c.y / H * NY) % NY];
}

function updateNutrition() {
  const next = Array.from({ length: NX }, () => Array.from({ length: NY }, () => 0));
  for (let i = 0; i < NX; i++) {
    const ip = (i + 1) % NX, im = (i - 1 + NX) % NX;
    for (let j = 0; j < NY; j++) {
      const jp = (j + 1) % NY, jm = (j - 1 + NY) % NY;
      const n = N[i][j], k = K[i][j];
      const growth = 0.02 * P[i][j] * n * (1 - n / Math.max(1e-6, k));
      const lap = N[ip][j] + N[im][j] + N[i][jp] + N[i][jm] - 4 * n;
      next[i][j] = Math.max(0, Math.min(k, n + growth + 0.12 * lap));
    }
  }
  for (let i = 0; i < NX; i++) for (let j = 0; j < NY; j++) N[i][j] = next[i][j];
}

function chooseVelocity(c) {
  if (c.species === 'H' && c.energy < 6) {
    const [i, j] = cellOf(c);
    let best = N[i][j], bi = i, bj = j;
    for (let di = -1; di <= 1; di++) {
      for (let dj = -1; dj <= 1; dj++) {
        const ii = (i + di + NX) % NX, jj = (j + dj + NY) % NY;
        if (N[ii][jj] > best) { best = N[ii][jj]; bi = ii; bj = jj; }
      }
    }
    const tx = (bi + 0.5) * CELL_W, ty = (bj + 0.5) * CELL_H;
    const dx = torusDelta(c.x, tx, W), dy = torusDelta(c.y, ty, H);
    const d = Math.max(1e-6, Math.hypot(dx, dy));
    c.vx = dx / d * c.speed; c.vy = dy / d * c.speed;
    return;
  }

  if (c.species === 'C' && c.energy < 7) {
    let target = null, best = Infinity;
    for (const o of creatures) {
      if (o.species !== 'H') continue;
      const d = torusDist(c, o);
      if (d < best && d < c.vision) { best = d; target = o; }
    }
    if (target) {
      const dx = torusDelta(c.x, target.x, W), dy = torusDelta(c.y, target.y, H);
      const d = Math.max(1e-6, Math.hypot(dx, dy));
      c.vx = dx / d * c.speed; c.vy = dy / d * c.speed;
      return;
    }
  }

  const a = Math.random() * Math.PI * 2;
  c.vx = Math.cos(a) * c.speed;
  c.vy = Math.sin(a) * c.speed;
}

function step() {
  tick++;
  for (const c of creatures) {
    chooseVelocity(c);
    c.x = wrap(c.x + c.vx, W);
    c.y = wrap(c.y + c.vy, H);
    c.age++;
    c.cooldown = Math.max(0, c.cooldown - 1);

    const [i, j] = cellOf(c);
    if (c.species === 'H') {
      const eat = Math.min(N[i][j], 0.8 * c.size);
      N[i][j] -= eat;
      c.energy += eat;
    }
  }

  for (const pred of creatures) {
    if (pred.species !== 'C' || pred.cooldown > 0) continue;
    for (const prey of creatures) {
      if (prey.species !== 'H') continue;
      if (torusDist(pred, prey) < 5 + prey.size) {
        prey.hp -= pred.attack;
        pred.energy -= 1.5;
        pred.cooldown = 10;
        if (prey.hp <= 0) {
          prey.dead = true;
          pred.energy += 15;
        }
        break;
      }
    }
  }

  for (const c of creatures) {
    c.energy -= 0.05 + 0.02 * Math.hypot(c.vx, c.vy);
    if (c.energy < 0) c.hp += c.energy;
    if (c.hp <= 0) c.dead = true;
  }

  creatures = creatures.filter(c => !c.dead);
  updateNutrition();
}

function draw() {
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#020611';
  ctx.fillRect(0, 0, W, H);

  ctx.strokeStyle = '#0f1f45';
  ctx.lineWidth = 1;
  for (let x = 0; x < W; x += 48) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 0; y < H; y += 48) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }

  for (let i = 0; i < NX; i += 2) {
    for (let j = 0; j < NY; j += 2) {
      const n = N[i][j] / Math.max(1e-6, K[i][j]);
      const e = elev[i][j];
      const g = Math.floor(20 + n * 170);
      const b = Math.floor(50 + e * 100);
      ctx.fillStyle = `rgba(${20 + b}, ${g}, ${110 + b}, 0.58)`;
      ctx.fillRect(i * CELL_W, j * CELL_H, CELL_W * 2, CELL_H * 2);
    }
  }

  for (const c of creatures) {
    const r = 2 + c.size * 1.6;
    const glow = c.species === 'H' ? '#00ff98' : '#ff4ca3';
    const core = c.species === 'H' ? '#80ff88' : '#ff7dbd';

    ctx.fillStyle = glow;
    ctx.globalAlpha = 0.15;
    ctx.beginPath(); ctx.arc(c.x, c.y, r * 3, 0, Math.PI * 2); ctx.fill();
    ctx.globalAlpha = 1;

    ctx.fillStyle = core;
    ctx.beginPath(); ctx.arc(c.x, c.y, r, 0, Math.PI * 2); ctx.fill();
  }

  const hf = creatures.filter(c => c.species === 'H' && c.sex === 'F').length;
  const hm = creatures.filter(c => c.species === 'H' && c.sex === 'M').length;
  const cf = creatures.filter(c => c.species === 'C' && c.sex === 'F').length;
  const cm = creatures.filter(c => c.species === 'C' && c.sex === 'M').length;
  const nsum = N.flat().reduce((a, b) => a + b, 0);
  statsEl.textContent = `tick=${tick} | H(F/M)=${hf}/${hm} | C(F/M)=${cf}/${cm} | nutrition=${nsum.toFixed(1)}`;
}

function loop() {
  if (running) step();
  draw();
  requestAnimationFrame(loop);
}

function injectRandom() {
  const cx = Math.floor(Math.random() * NX);
  const cy = Math.floor(Math.random() * NY);
  for (let i = 0; i < NX; i++) {
    for (let j = 0; j < NY; j++) {
      const di = Math.min(Math.abs(i - cx), NX - Math.abs(i - cx));
      const dj = Math.min(Math.abs(j - cy), NY - Math.abs(j - cy));
      if (di * di + dj * dj < 25) N[i][j] = Math.min(K[i][j], N[i][j] + 2.2);
    }
  }
}

function meteor() {
  const x = Math.random() * W;
  const y = Math.random() * H;
  for (const c of creatures) {
    const dx = torusDelta(x, c.x, W);
    const dy = torusDelta(y, c.y, H);
    if (dx * dx + dy * dy < 50 * 50) c.dead = true;
  }
}

function disease() {
  for (const c of creatures) {
    if (Math.random() < 0.2) c.hp *= 0.65;
  }
}

document.getElementById('toggle').onclick = () => {
  running = !running;
  document.getElementById('toggle').textContent = running ? 'Pause' : 'Resume';
};
document.getElementById('inject').onclick = injectRandom;
document.getElementById('meteor').onclick = meteor;
document.getElementById('disease').onclick = disease;

loop();
