from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Game, User


SEED_AUTHOR_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
SEED_BUNDLE_REV = "20260620-play-stage-only-v3"


@dataclass(frozen=True)
class SeedGameDefinition:
    game_id: uuid.UUID
    title: str
    description: str
    tags: list[str]
    play_count: int
    like_count: int
    cover_label: str
    controls: list[str]
    theme_color: str
    game_kind: str


SEED_GAME_DEFINITIONS: Sequence[SeedGameDefinition] = (
    SeedGameDefinition(
        game_id=uuid.UUID("11111111-aaaa-4444-8888-111111111111"),
        title="Sky Runner",
        description="A fast mock platformer with floating islands and coin trails.",
        tags=["runner", "arcade"],
        play_count=12400,
        like_count=8200,
        cover_label="Sky Runner",
        controls=[
            "ArrowLeft / ArrowRight to move",
            "Space to jump",
        ],
        theme_color="#ffc200",
        game_kind="sky-runner",
    ),
    SeedGameDefinition(
        game_id=uuid.UUID("22222222-bbbb-5555-9999-222222222222"),
        title="Pixel Raid",
        description="A mock co-op raid prototype with short arena battles.",
        tags=["action", "co-op"],
        play_count=9800,
        like_count=5700,
        cover_label="Pixel Raid",
        controls=[
            "WASD to move",
            "Move cursor to aim",
        ],
        theme_color="#6cf5c2",
        game_kind="pixel-raid",
    ),
)


def _seed_author_defaults() -> dict:
    return {
        "user_id": SEED_AUTHOR_ID,
        "email": "seed-author@example.com",
        "display_name": "Yahaha Seeds",
        "password_hash": None,
    }


def _cover_svg(title: str, theme_color: str) -> bytes:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#17212b" />
      <stop offset="100%" stop-color="#0f1112" />
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#bg)" />
  <circle cx="980" cy="160" r="110" fill="{theme_color}" opacity="0.9" />
  <rect x="96" y="470" width="520" height="120" rx="28" fill="#12161b" opacity="0.88" />
  <text x="128" y="545" fill="#ffffff" font-size="56" font-family="Arial, sans-serif">{title}</text>
</svg>"""
    return svg.encode("utf-8")


def _index_html(definition: SeedGameDefinition) -> bytes:
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{definition.title}</title>
    <link rel="stylesheet" href="style.css?v={SEED_BUNDLE_REV}" />
  </head>
  <body>
    <main id="app">
      <section class="game-shell">
        <div class="scoreboard" id="scoreboard" aria-live="polite">
          <span id="status-label">Loading</span>
          <strong id="score-value">0</strong>
        </div>
        <canvas id="game-canvas" width="960" height="540" tabindex="0" aria-label="{definition.title} game canvas"></canvas>
        <p class="sr-only" id="hint-text">Booting {definition.title}...</p>
      </section>
    </main>
    <script src="game.js?v={SEED_BUNDLE_REV}"></script>
  </body>
</html>"""
    return html.encode("utf-8")


def _style_css(definition: SeedGameDefinition) -> bytes:
    css = """
html, body {
  margin: 0;
  width: 100%;
  height: 100%;
  min-height: 100%;
  overflow: hidden;
  background: transparent;
  color: #ffffff;
  font-family: Arial, sans-serif;
}

body {
  display: block;
  padding: 0;
  box-sizing: border-box;
}

#app {
  width: 100%;
  height: 100%;
  padding: 0;
  box-sizing: border-box;
  overflow: hidden;
}

.scoreboard {
  position: absolute;
  top: 18px;
  left: 18px;
  z-index: 2;
  display: grid;
  gap: 2px;
  min-width: 124px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(10, 12, 13, 0.62);
  backdrop-filter: blur(14px);
}

.scoreboard {
  padding: 12px 14px;
  border-radius: 16px;
  text-align: left;
}

#status-label {
  display: block;
  color: #9aa6b2;
  font-size: 12px;
}

#score-value {
  font-size: 28px;
  color: __THEME_COLOR__;
}

#game-canvas {
  display: block;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  background: #0f141a;
}

.game-shell {
  position: relative;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 1040px) {
  .scoreboard {
    top: 12px;
    left: 12px;
  }
}
""".replace("__THEME_COLOR__", definition.theme_color).strip()
    return css.encode("utf-8")


def _sky_runner_js() -> bytes:
    script = """
const canvas = document.getElementById("game-canvas");
const ctx = canvas.getContext("2d");
const scoreValue = document.getElementById("score-value");
const statusLabel = document.getElementById("status-label");
const hintText = document.getElementById("hint-text");

const state = {
  keys: {},
  time: 0,
  coinsCollected: 0,
  speed: 6,
  player: { x: 110, y: 390, width: 42, height: 52, vx: 0, vy: 0, onGround: false },
  obstacles: [],
  coins: [],
};

function spawnObstacle() {
  state.obstacles.push({
    x: canvas.width + 40,
    y: 412,
    width: 26 + Math.random() * 28,
    height: 38 + Math.random() * 26,
  });
}

function spawnCoin() {
  state.coins.push({
    x: canvas.width + 30,
    y: 220 + Math.random() * 110,
    radius: 10,
    taken: false,
  });
}

window.addEventListener("keydown", (event) => {
  if (["ArrowLeft", "ArrowRight", "Space"].includes(event.code)) {
    event.preventDefault();
  }
  state.keys[event.code] = true;
  if (event.code === "Space" && state.player.onGround) {
    state.player.vy = -15;
    state.player.onGround = false;
  }
});

window.addEventListener("keyup", (event) => {
  state.keys[event.code] = false;
});

function update() {
  state.time += 1;
  const player = state.player;

  player.vx = 0;
  if (state.keys.ArrowLeft) player.vx = -5;
  if (state.keys.ArrowRight) player.vx = 5;

  player.x = Math.max(50, Math.min(280, player.x + player.vx));
  player.vy += 0.75;
  player.y += player.vy;

  if (player.y >= 390) {
    player.y = 390;
    player.vy = 0;
    player.onGround = true;
  }

  if (state.time % 90 === 0) spawnObstacle();
  if (state.time % 65 === 0) spawnCoin();

  for (const obstacle of state.obstacles) {
    obstacle.x -= state.speed;
  }
  for (const coin of state.coins) {
    coin.x -= state.speed;
  }

  state.obstacles = state.obstacles.filter((obstacle) => obstacle.x + obstacle.width > -20);
  state.coins = state.coins.filter((coin) => coin.x + coin.radius > -20 && !coin.taken);

  for (const coin of state.coins) {
    const dx = coin.x - (player.x + player.width / 2);
    const dy = coin.y - (player.y + player.height / 2);
    if (Math.hypot(dx, dy) < coin.radius + 18) {
      coin.taken = true;
      state.coinsCollected += 1;
    }
  }

  for (const obstacle of state.obstacles) {
    const hit =
      player.x < obstacle.x + obstacle.width &&
      player.x + player.width > obstacle.x &&
      player.y < obstacle.y + obstacle.height &&
      player.y + player.height > obstacle.y;
    if (hit) {
      state.coinsCollected = Math.max(0, state.coinsCollected - 2);
      obstacle.x = -100;
    }
  }
}

function draw() {
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, "#263648");
  gradient.addColorStop(1, "#101418");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#8fc7ff";
  ctx.fillRect(0, 430, canvas.width, 110);

  ctx.fillStyle = "#ffc200";
  for (const coin of state.coins) {
    ctx.beginPath();
    ctx.arc(coin.x, coin.y, coin.radius, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.fillStyle = "#ff7a59";
  for (const obstacle of state.obstacles) {
    ctx.fillRect(obstacle.x, obstacle.y, obstacle.width, obstacle.height);
  }

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(state.player.x, state.player.y, state.player.width, state.player.height);

  ctx.fillStyle = "#0f141a";
  ctx.font = "bold 24px Arial";
  ctx.fillText(`Coins ${state.coinsCollected}`, 22, 38);
}

function tick() {
  update();
  draw();
  scoreValue.textContent = String(state.coinsCollected);
  statusLabel.textContent = "Coins";
  if (hintText) hintText.textContent = "Dodge lava blocks and collect coins on the skyline.";
  requestAnimationFrame(tick);
}

requestAnimationFrame(tick);
""".strip()
    return script.encode("utf-8")


def _pixel_raid_js() -> bytes:
    script = """
const canvas = document.getElementById("game-canvas");
const ctx = canvas.getContext("2d");
const scoreValue = document.getElementById("score-value");
const statusLabel = document.getElementById("status-label");
const hintText = document.getElementById("hint-text");

const state = {
  keys: {},
  pointer: { x: canvas.width / 2, y: canvas.height / 2 },
  bullets: [],
  enemies: [],
  score: 0,
  frame: 0,
  player: { x: canvas.width / 2, y: canvas.height / 2, radius: 16, hp: 5, speed: 3.8 },
};

function spawnEnemy() {
  const edge = Math.floor(Math.random() * 4);
  const spawn = [
    { x: Math.random() * canvas.width, y: -30 },
    { x: canvas.width + 30, y: Math.random() * canvas.height },
    { x: Math.random() * canvas.width, y: canvas.height + 30 },
    { x: -30, y: Math.random() * canvas.height },
  ][edge];
  state.enemies.push({ ...spawn, radius: 14, speed: 1.3 + Math.random() * 0.9 });
}

window.addEventListener("keydown", (event) => {
  if (["KeyW", "KeyA", "KeyS", "KeyD", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Space"].includes(event.code)) {
    event.preventDefault();
  }
  state.keys[event.code] = true;
});

window.addEventListener("keyup", (event) => {
  state.keys[event.code] = false;
});

canvas.addEventListener("mousemove", (event) => {
  const rect = canvas.getBoundingClientRect();
  state.pointer.x = (event.clientX - rect.left) * (canvas.width / rect.width);
  state.pointer.y = (event.clientY - rect.top) * (canvas.height / rect.height);
});

function fireBullet() {
  const angle = Math.atan2(state.pointer.y - state.player.y, state.pointer.x - state.player.x);
  state.bullets.push({
    x: state.player.x,
    y: state.player.y,
    vx: Math.cos(angle) * 7,
    vy: Math.sin(angle) * 7,
    radius: 4,
  });
}

function update() {
  state.frame += 1;
  if (state.frame % 22 === 0) fireBullet();
  if (state.frame % 45 === 0) spawnEnemy();

  const moveX = (state.keys.KeyD ? 1 : 0) - (state.keys.KeyA ? 1 : 0);
  const moveY = (state.keys.KeyS ? 1 : 0) - (state.keys.KeyW ? 1 : 0);
  const length = Math.hypot(moveX, moveY) || 1;
  state.player.x = Math.max(20, Math.min(canvas.width - 20, state.player.x + (moveX / length) * state.player.speed));
  state.player.y = Math.max(20, Math.min(canvas.height - 20, state.player.y + (moveY / length) * state.player.speed));

  for (const bullet of state.bullets) {
    bullet.x += bullet.vx;
    bullet.y += bullet.vy;
  }
  state.bullets = state.bullets.filter((bullet) => bullet.x > -10 && bullet.x < canvas.width + 10 && bullet.y > -10 && bullet.y < canvas.height + 10);

  for (const enemy of state.enemies) {
    const angle = Math.atan2(state.player.y - enemy.y, state.player.x - enemy.x);
    enemy.x += Math.cos(angle) * enemy.speed;
    enemy.y += Math.sin(angle) * enemy.speed;
  }

  for (const enemy of state.enemies) {
    for (const bullet of state.bullets) {
      if (Math.hypot(enemy.x - bullet.x, enemy.y - bullet.y) < enemy.radius + bullet.radius) {
        enemy.radius = 0;
        bullet.x = -100;
        state.score += 1;
      }
    }
    if (Math.hypot(enemy.x - state.player.x, enemy.y - state.player.y) < enemy.radius + state.player.radius) {
      enemy.radius = 0;
      state.player.hp = Math.max(0, state.player.hp - 1);
    }
  }

  state.enemies = state.enemies.filter((enemy) => enemy.radius > 0);
}

function draw() {
  ctx.fillStyle = "#0c1318";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = "rgba(255,255,255,0.06)";
  for (let x = 0; x < canvas.width; x += 48) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += 48) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.stroke();
  }

  ctx.fillStyle = "#6cf5c2";
  ctx.beginPath();
  ctx.arc(state.player.x, state.player.y, state.player.radius, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#8ee7ff";
  for (const bullet of state.bullets) {
    ctx.beginPath();
    ctx.arc(bullet.x, bullet.y, bullet.radius, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.fillStyle = "#ff6d9d";
  for (const enemy of state.enemies) {
    ctx.beginPath();
    ctx.arc(enemy.x, enemy.y, enemy.radius, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 24px Arial";
  ctx.fillText(`Raid ${state.score}`, 22, 38);
  ctx.fillText(`HP ${state.player.hp}`, 22, 68);
}

function tick() {
  update();
  draw();
  scoreValue.textContent = String(state.score);
  statusLabel.textContent = `HP ${state.player.hp}`;
  if (hintText) hintText.textContent = "Survive the neon raid by kiting enemies and auto-firing.";
  requestAnimationFrame(tick);
}

requestAnimationFrame(tick);
""".strip()
    return script.encode("utf-8")


def _manifest(definition: SeedGameDefinition) -> bytes:
    manifest = {
        "schemaVersion": "1.0",
        "title": definition.title,
        "description": definition.description,
        "entry": "index.html",
        "styles": ["style.css"],
        "scripts": ["game.js"],
        "assets": ["assets/cover.svg"],
        "cover": "assets/cover.svg",
        "controls": definition.controls,
        "runtime": "html5-iframe",
        "generatedAt": "2026-06-20T05:08:00Z",
    }
    return json.dumps(manifest, ensure_ascii=True).encode("utf-8")


def _bundle_files(definition: SeedGameDefinition) -> dict[str, tuple[bytes, str]]:
    if definition.game_kind == "sky-runner":
        game_js = _sky_runner_js()
    elif definition.game_kind == "pixel-raid":
        game_js = _pixel_raid_js()
    else:
        raise ValueError(f"Unsupported seed game kind: {definition.game_kind}")

    return {
        "manifest.json": (_manifest(definition), "application/json"),
        "index.html": (_index_html(definition), "text/html; charset=utf-8"),
        "style.css": (_style_css(definition), "text/css; charset=utf-8"),
        "game.js": (game_js, "application/javascript; charset=utf-8"),
        "assets/cover.svg": (
            _cover_svg(definition.cover_label, definition.theme_color),
            "image/svg+xml",
        ),
    }


async def seed_published_games(session: AsyncSession, storage) -> list[Game]:
    author = await session.get(User, SEED_AUTHOR_ID)
    if author is None:
        author = User(**_seed_author_defaults())
        session.add(author)
        await session.flush()

    created_games: list[Game] = []
    now = datetime.now(timezone.utc)

    for index, definition in enumerate(SEED_GAME_DEFINITIONS):
        version = "v1"
        manifest_key = storage.build_published_object_key(
            game_id=definition.game_id,
            version=version,
            relative_path="manifest.json",
        )
        index_key = storage.build_published_object_key(
            game_id=definition.game_id,
            version=version,
            relative_path="index.html",
        )
        artifact_base_url = storage.build_public_read_url(index_key).rsplit("/", 1)[0] + "/"
        cover_key = storage.build_published_object_key(
            game_id=definition.game_id,
            version=version,
            relative_path="assets/cover.svg",
        )

        game = await session.get(Game, definition.game_id)
        if game is None:
            game = Game(
                id=definition.game_id,
                owner_id=author.user_id,
                title=definition.title,
                description=definition.description,
                cover_url=storage.build_public_read_url(cover_key),
                tags=definition.tags,
                status="published",
                manifest_url=storage.build_public_read_url(manifest_key),
                artifact_base_url=artifact_base_url,
                play_count=definition.play_count,
                like_count=definition.like_count,
                published_at=now - timedelta(days=index),
            )
            session.add(game)
        else:
            game.owner_id = author.user_id
            game.title = definition.title
            game.description = definition.description
            game.cover_url = storage.build_public_read_url(cover_key)
            game.tags = definition.tags
            game.status = "published"
            game.manifest_url = storage.build_public_read_url(manifest_key)
            game.artifact_base_url = artifact_base_url
            game.play_count = definition.play_count
            game.like_count = definition.like_count
            game.published_at = now - timedelta(days=index)

        for relative_path, (body, content_type) in _bundle_files(definition).items():
            object_key = storage.build_published_object_key(
                game_id=definition.game_id,
                version=version,
                relative_path=relative_path,
            )
            storage.put_object(object_key, body=body, content_type=content_type)

        created_games.append(game)

    await session.commit()

    result = (
        await session.execute(
            select(Game)
            .where(Game.id.in_([definition.game_id for definition in SEED_GAME_DEFINITIONS]))
            .order_by(Game.created_at.asc())
        )
    ).scalars().all()
    return result
