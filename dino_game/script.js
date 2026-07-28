const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

const overlay = document.getElementById('overlay');
const overlayTitle = document.getElementById('overlayTitle');
const overlayText = document.getElementById('overlayText');
const startBtn = document.getElementById('startBtn');

const DINO_IMAGE_PATH = 'assets/dino1.jpg';
let dinoImage = new Image();
let processedDinoImage = null;
dinoImage.onload = () => {
  processedDinoImage = createTransparentSprite(dinoImage);
  drawGame();
};
dinoImage.src = DINO_IMAGE_PATH;

const WIDTH = canvas.width;
const HEIGHT = canvas.height;
const GROUND_Y = 340;
const BASE_SPEED = 6;
const MAX_SPEED = 16;
const SPEED_PER_LEVEL = 0.6;
const POINTS_PER_LEVEL = 300;
const BASE_POINTS_PER_FRAME = 0.17;
const SHIELD_DURATION_FRAMES = 60 * 8;
const SLOWMO_DURATION_FRAMES = 60 * 5;
const BOOST_DURATION_FRAMES = 60 * 6;
const SLOWMO_FACTOR = 0.5;
const SCORE_BOOST_MULTIPLIER = 2;

let state = null;
let lastTime = 0;
let animationFrame = null;
let gameStarted = false;

function resetGame() {
  state = {
    dino: createDino(),
    obstacles: [],
    powerUps: [],
    score: 0,
    highScore: Number(localStorage.getItem('dinoHighScore') || 0),
    level: 1,
    speed: BASE_SPEED,
    effectiveSpeed: BASE_SPEED,
    gameOver: false,
    shieldFrames: 0,
    slowmoFrames: 0,
    boostFrames: 0,
    obstacleTimer: randomInt(70, 130),
    powerupTimer: randomInt(400, 700),
    clouds: [
      { x: 110, y: 70, speed: 0.6 },
      { x: 340, y: 98, speed: 0.6 },
      { x: 620, y: 56, speed: 0.6 },
    ],
    groundOffset: 0,
  };

  hideOverlay();
  gameStarted = true;
}

function createDino() {
  return {
    x: 86,
    y: GROUND_Y - 92,
    width: 72,
    height: 92,
    velocityY: 0,
    jumping: false,
    ducking: false,
    shieldActive: false,
    legTimer: 0,
    legUp: true,
    runCycle: 0,
  };
}

function startGame() {
  if (!state || state.gameOver) {
    resetGame();
  }
  hideOverlay();
}

function showOverlay(show = true, title = 'Dino Run', text = 'Jump over obstacles and duck under birds.') {
  overlayTitle.textContent = title;
  overlayText.textContent = text;
  overlay.classList.toggle('hidden', !show);
}

function hideOverlay() {
  overlay.classList.add('hidden');
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function handleInput(event) {
  if (!gameStarted) return;
  if (event.type === 'keydown') {
    if (event.code === 'Escape') {
      gameStarted = false;
      showOverlay(true, 'Paused', 'Press Start Game to continue.');
      return;
    }

    if (event.code === 'Space' || event.code === 'ArrowUp') {
      event.preventDefault();
      if (state.gameOver) {
        resetGame();
      } else if (!state.dino.jumping && !state.dino.ducking) {
        state.dino.velocityY = -15;
        state.dino.jumping = true;
      }
    }

    if (event.code === 'ArrowDown') {
      event.preventDefault();
      state.dino.ducking = true;
    }
  }

  if (event.type === 'keyup' && event.code === 'ArrowDown') {
    state.dino.ducking = false;
  }
}

function updateGame() {
  if (!state || !gameStarted || state.gameOver) return;

  const dino = state.dino;
  if (dino.jumping) {
    const gravity = dino.ducking ? 1.6 : 0.8;
    dino.velocityY += gravity;
    dino.y += dino.velocityY;
    if (dino.y >= GROUND_Y - dino.height) {
      dino.y = GROUND_Y - dino.height;
      dino.velocityY = 0;
      dino.jumping = false;
    }
  } else {
    dino.y = GROUND_Y - dino.height;
  }

  dino.width = dino.ducking && !dino.jumping ? 66 : 72;
  dino.height = dino.ducking && !dino.jumping ? 68 : 92;

  if (!dino.jumping) {
    dino.legTimer += 1;
    if (dino.legTimer >= 6) {
      dino.legTimer = 0;
      dino.legUp = !dino.legUp;
    }
    dino.runCycle = (dino.runCycle + 1) % 8;
  }

  state.groundOffset += state.effectiveSpeed;
  state.clouds.forEach((cloud) => {
    cloud.x -= cloud.speed;
  });
  state.clouds = state.clouds.filter((cloud) => cloud.x + 70 > 0);
  while (state.clouds.length < 3) {
    state.clouds.push({ x: WIDTH + 30, y: 50 + 22 * state.clouds.length, speed: 0.6 });
  }

  state.effectiveSpeed = state.speed * (state.slowmoFrames > 0 ? SLOWMO_FACTOR : 1.0);
  state.obstacles.forEach((obstacle) => {
    obstacle.x -= state.effectiveSpeed;
  });
  state.powerUps.forEach((powerUp) => {
    powerUp.x -= state.effectiveSpeed;
  });

  state.obstacles = state.obstacles.filter((obstacle) => obstacle.x + obstacle.width > 0);
  state.powerUps = state.powerUps.filter((powerUp) => powerUp.x + powerUp.radius > 0);

  state.obstacleTimer -= 1;
  if (state.obstacleTimer <= 0) {
    state.obstacles.push(spawnObstacle());
    const gapMin = Math.max(45, 70 - state.level * 4);
    const gapMax = Math.max(gapMin + 20, 130 - state.level * 6);
    state.obstacleTimer = randomInt(gapMin, gapMax);
  }

  state.powerupTimer -= 1;
  if (state.powerupTimer <= 0) {
    state.powerUps.push(spawnPowerUp());
    state.powerupTimer = randomInt(400, 700);
  }

  if (state.shieldFrames > 0) state.shieldFrames -= 1;
  if (state.slowmoFrames > 0) state.slowmoFrames -= 1;
  if (state.boostFrames > 0) state.boostFrames -= 1;

  state.dino.shieldActive = state.shieldFrames > 0;
  state.score += BASE_POINTS_PER_FRAME * (state.boostFrames > 0 ? SCORE_BOOST_MULTIPLIER : 1);

  const targetLevel = 1 + Math.floor(state.score / POINTS_PER_LEVEL);
  if (targetLevel > state.level) {
    state.level = targetLevel;
    state.speed = Math.min(MAX_SPEED, BASE_SPEED + (state.level - 1) * SPEED_PER_LEVEL);
  }

  checkCollisions();
}

function spawnObstacle() {
  if (Math.random() < 0.65) {
    const size = Math.random() < 0.7 ? 'small' : 'large';
    const width = size === 'large' ? 40 : randomInt(20, 35);
    const height = size === 'large' ? 72 : 48;
    return { x: WIDTH + 20, y: GROUND_Y - height, width, height, kind: 'cactus' };
  }

  const variant = Math.random() < 0.5 ? 'high' : 'low';
  return {
    x: WIDTH + 20,
    y: variant === 'high' ? GROUND_Y - 72 : GROUND_Y - 38,
    width: 44,
    height: 30,
    kind: 'bird',
    variant,
    wingUp: true,
  };
}

function spawnPowerUp() {
  const kind = ['shield', 'slowmo', 'boost'][Math.floor(Math.random() * 3)];
  return { x: WIDTH + 20, y: GROUND_Y - 90, radius: 16, kind };
}

function checkCollisions() {
  const dinoRect = {
    x: state.dino.x,
    y: state.dino.y,
    width: state.dino.width,
    height: state.dino.height,
  };

  for (let i = state.obstacles.length - 1; i >= 0; i -= 1) {
    const obstacle = state.obstacles[i];
    const rect = { x: obstacle.x, y: obstacle.y, width: obstacle.width, height: obstacle.height };
    if (rectIntersect(dinoRect, rect)) {
      if (state.shieldFrames > 0) {
        state.shieldFrames = 0;
        state.obstacles.splice(i, 1);
      } else {
        endGame();
      }
      break;
    }
  }

  for (let i = state.powerUps.length - 1; i >= 0; i -= 1) {
    const powerUp = state.powerUps[i];
    const rect = { x: powerUp.x - powerUp.radius, y: powerUp.y - powerUp.radius, width: powerUp.radius * 2, height: powerUp.radius * 2 };
    if (rectIntersect(dinoRect, rect)) {
      collectPowerUp(powerUp.kind);
      state.powerUps.splice(i, 1);
    }
  }
}

function collectPowerUp(kind) {
  if (kind === 'shield') {
    state.shieldFrames = SHIELD_DURATION_FRAMES;
  } else if (kind === 'slowmo') {
    state.slowmoFrames = SLOWMO_DURATION_FRAMES;
  } else if (kind === 'boost') {
    state.boostFrames = BOOST_DURATION_FRAMES;
  }
}

function endGame() {
  state.gameOver = true;
  if (state.score > state.highScore) {
    state.highScore = state.score;
    localStorage.setItem('dinoHighScore', String(Math.floor(state.highScore)));
  }
  showOverlay(true, 'Game Over', 'Press Space or Up to play again.');
}

function drawGame() {
  ctx.clearRect(0, 0, WIDTH, HEIGHT);
  drawBackground();
  drawClouds();
  drawObstacles();
  drawPowerUps();
  drawDino();
}

function drawBackground() {
  const sky = ctx.createLinearGradient(0, 0, 0, HEIGHT);
  sky.addColorStop(0, '#8fdcff');
  sky.addColorStop(1, '#f3fbff');
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  ctx.fillStyle = '#ffd56f';
  ctx.beginPath();
  ctx.arc(WIDTH - 70, 64, 32, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = '#6bbd5c';
  ctx.beginPath();
  ctx.moveTo(0, GROUND_Y - 8);
  ctx.quadraticCurveTo(120, GROUND_Y - 42, 260, GROUND_Y - 10);
  ctx.quadraticCurveTo(430, GROUND_Y + 16, 620, GROUND_Y - 8);
  ctx.quadraticCurveTo(760, GROUND_Y - 24, WIDTH, GROUND_Y - 8);
  ctx.lineTo(WIDTH, HEIGHT);
  ctx.lineTo(0, HEIGHT);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = '#7b4b2b';
  ctx.fillRect(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y);
  ctx.strokeStyle = '#4d3119';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(0, GROUND_Y);
  ctx.lineTo(WIDTH, GROUND_Y);
  ctx.stroke();

  ctx.strokeStyle = '#5e4022';
  ctx.lineWidth = 2;
  for (let x = -Math.floor(state.groundOffset) % 40; x < WIDTH; x += 40) {
    ctx.beginPath();
    ctx.moveTo(x, GROUND_Y + 14);
    ctx.lineTo(x + 20, GROUND_Y + 14);
    ctx.stroke();
  }
}

function drawClouds() {
  ctx.fillStyle = 'rgba(255,255,255,0.92)';
  state.clouds.forEach((cloud) => {
    ctx.beginPath();
    ctx.ellipse(cloud.x, cloud.y, 24, 14, 0, 0, Math.PI * 2);
    ctx.ellipse(cloud.x + 18, cloud.y - 8, 18, 12, 0, 0, Math.PI * 2);
    ctx.fill();
  });
}

function drawObstacles() {
  state.obstacles.forEach((obstacle) => {
    if (obstacle.kind === 'cactus') {
      drawCactus(obstacle);
    } else {
      drawBird(obstacle);
    }
  });
}

function drawCactus(obstacle) {
  const { x, y, width, height } = obstacle;
  ctx.fillStyle = '#2e7d3b';
  const trunkW = width * 0.55;
  const trunkX = x + (width - trunkW) / 2;
  roundRect(ctx, trunkX, y, trunkW, height, trunkW / 2, true);
  ctx.fillStyle = '#2a642f';
  const armW = Math.max(8, width * 0.28);
  roundRect(ctx, trunkX - armW * 0.75, y + height * 0.35, armW * 0.8, armW * 0.55, 6, true);
  roundRect(ctx, trunkX - armW * 0.75, y + height * 0.2 - armW * 0.7, armW * 0.55, armW * 0.75, 6, true);
  roundRect(ctx, trunkX + trunkW - armW * 0.15, y + height * 0.2, armW * 0.8, armW * 0.55, 6, true);
  roundRect(ctx, trunkX + trunkW + armW * 0.55, y + height * 0.1 - armW * 0.7, armW * 0.55, armW * 0.75, 6, true);
}

function drawBird(obstacle) {
  const { x, y, width, height, wingUp } = obstacle;
  ctx.fillStyle = '#d94e44';
  ctx.beginPath();
  ctx.ellipse(x + width * 0.4, y + height * 0.43, width * 0.35, height * 0.32, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = '#8f2a24';
  ctx.beginPath();
  ctx.moveTo(x + width * 0.12, y + height * 0.48);
  ctx.lineTo(x - width * 0.08, y + height * 0.25);
  ctx.lineTo(x - width * 0.08, y + height * 0.68);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = '#f4b93e';
  ctx.beginPath();
  ctx.moveTo(x + width * 0.70, y + height * 0.38);
  ctx.lineTo(x + width * 0.92, y + height * 0.33);
  ctx.lineTo(x + width * 0.70, y + height * 0.48);
  ctx.closePath();
  ctx.fill();

  ctx.strokeStyle = '#7d211d';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(x + width * 0.36, y + height * 0.42);
  ctx.lineTo(x + width * 0.15, wingUp ? y + height * 0.1 : y + height * 0.62);
  ctx.stroke();
}

function drawPowerUps() {
  state.powerUps.forEach((powerUp) => {
    const { x, y, radius, kind } = powerUp;
    const colors = {
      shield: ['#f7b53b', '#ffe19b'],
      slowmo: ['#3b82f6', '#bfdbfe'],
      boost: ['#9b5de5', '#dfc4ff'],
    };

    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = colors[kind][0];
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = colors[kind][1];
    ctx.beginPath();
    ctx.arc(x, y, radius * 0.55, 0, Math.PI * 2);
    ctx.fill();
  });
}

function createTransparentSprite(source) {
  const canvas = document.createElement('canvas');
  const width = source.naturalWidth || source.width || 128;
  const height = source.naturalHeight || source.height || 128;
  canvas.width = width;
  canvas.height = height;

  const spriteCtx = canvas.getContext('2d');
  spriteCtx.drawImage(source, 0, 0, width, height);

  const imageData = spriteCtx.getImageData(0, 0, width, height);
  const data = imageData.data;
  for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    const a = data[i + 3];
    const brightness = (r + g + b) / 3;
    const isBackground = a > 160 && brightness > 220 && Math.abs(r - g) < 18 && Math.abs(g - b) < 18 && Math.abs(r - b) < 18;
    if (isBackground) {
      data[i + 3] = 0;
    }
  }
  spriteCtx.putImageData(imageData, 0, 0);

  const processed = new Image();
  processed.src = canvas.toDataURL('image/png');
  return processed;
}

function drawDino() {
  const dino = state.dino;
  const x = dino.x;
  const y = dino.y;
  const w = dino.width;
  const h = dino.height;
  const sprite = processedDinoImage || dinoImage;

  if (sprite && sprite.complete) {
    ctx.save();
    if (dino.shieldActive) {
      ctx.strokeStyle = '#ffd77a';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.ellipse(x + w * 0.54, y + h * 0.52, w * 0.48 + 6, h * 0.48 + 6, 0, 0, Math.PI * 2);
      ctx.stroke();
    }

    const drawW = w * 1.24;
    const drawH = h * 1.2;
    const drawX = x - (drawW - w) / 2;
    const drawY = y - (drawH - h) / 2 + (dino.ducking ? 6 : 0);

    const bob = dino.jumping ? -6 : dino.ducking ? 0 : dino.legUp ? -4 : 4;
    const stretch = dino.jumping ? 1.06 : dino.ducking ? 0.95 : dino.legUp ? 1.02 : 0.98;
    const tilt = dino.jumping ? -0.05 : dino.ducking ? 0.03 : dino.legUp ? 0.03 : -0.03;
    const bounce = dino.jumping ? 0 : Math.sin(dino.runCycle / 2) * 1.6;

    ctx.translate(drawX + drawW / 2, drawY + drawH / 2);
    ctx.scale(-1, 1);
    ctx.rotate(tilt);
    ctx.scale(1, stretch);
    ctx.translate(-(drawX + drawW / 2), -(drawY + drawH / 2));
    ctx.translate(0, bob + bounce);
    ctx.drawImage(sprite, drawX, drawY, drawW, drawH);
    ctx.restore();
  }
}

function roundRect(context, x, y, width, height, radius, fill = true) {
  const r = Math.min(radius, width / 2, height / 2);
  context.beginPath();
  context.moveTo(x + r, y);
  context.arcTo(x + width, y, x + width, y + height, r);
  context.arcTo(x + width, y + height, x, y + height, r);
  context.arcTo(x, y + height, x, y, r);
  context.arcTo(x, y, x + width, y, r);
  context.closePath();
  if (fill) {
    context.fill();
  } else {
    context.stroke();
  }
}

function rectIntersect(a, b) {
  return a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
}

function loop(timestamp) {
  if (!lastTime) lastTime = timestamp;
  const delta = timestamp - lastTime;
  lastTime = timestamp;
  if (delta > 0) {
    updateGame(delta);
    drawGame();
  }
  animationFrame = requestAnimationFrame(loop);
}

function init() {
  resetGame();
  showOverlay(true, 'Dino Run', 'Jump over obstacles and duck under birds.');
  startBtn.addEventListener('click', startGame);
  document.addEventListener('keydown', handleInput);
  document.addEventListener('keyup', handleInput);
  animationFrame = requestAnimationFrame(loop);
}

init();
