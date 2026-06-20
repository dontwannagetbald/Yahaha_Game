from __future__ import annotations

import json
from pathlib import Path


INDEX_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <main id="game">
      <h1>{title}</h1>
      <p>{description}</p>
      <p id="status">使用方向键移动，收集能量并躲避障碍。</p>
      <div id="hud">
        <span id="timer">60</span>
        <span id="score">0</span>
      </div>
      <canvas id="stage" width="960" height="540"></canvas>
    </main>
    <script src="game.js"></script>
  </body>
</html>
"""


STYLE_TEMPLATE = """
html, body {
  margin: 0;
  min-height: 100%;
  background: #09111f;
  color: #f7fafc;
  font-family: Inter, Arial, sans-serif;
}

#game {
  display: grid;
  place-items: center;
  gap: 16px;
  min-height: 100vh;
}

#stage {
  border: 2px solid rgba(255, 255, 255, 0.2);
  background: radial-gradient(circle at top, #103a66, #08101c 60%);
}
"""


SCRIPT_TEMPLATE = """
const canvas = document.getElementById('stage');
const ctx = canvas.getContext('2d');
const player = { x: 120, y: 120, size: 28 };
const keys = new Set();
let score = 0;

window.addEventListener('keydown', (event) => keys.add(event.key));
window.addEventListener('keyup', (event) => keys.delete(event.key));

function tick() {
  if (keys.has('ArrowUp') || keys.has('w')) player.y -= 3;
  if (keys.has('ArrowDown') || keys.has('s')) player.y += 3;
  if (keys.has('ArrowLeft') || keys.has('a')) player.x -= 3;
  if (keys.has('ArrowRight') || keys.has('d')) player.x += 3;
  player.x = Math.max(0, Math.min(canvas.width - player.size, player.x));
  player.y = Math.max(0, Math.min(canvas.height - player.size, player.y));
  score += 1;
  document.getElementById('score').textContent = String(score);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#ffc200';
  ctx.fillRect(player.x, player.y, player.size, player.size);
  ctx.fillStyle = '#7dd3fc';
  ctx.beginPath();
  ctx.arc(760, 160, 16, 0, Math.PI * 2);
  ctx.fill();

  requestAnimationFrame(tick);
}

requestAnimationFrame(tick);
window.parent?.postMessage?.({ type: 'game_ready' }, '*');
"""


def write_bundle(output_dir: Path, title: str, description: str, manifest: dict[str, object]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(
        INDEX_TEMPLATE.format(title=title, description=description),
        encoding="utf-8",
    )
    (output_dir / "style.css").write_text(STYLE_TEMPLATE.strip() + "\n", encoding="utf-8")
    (output_dir / "game.js").write_text(SCRIPT_TEMPLATE.strip() + "\n", encoding="utf-8")
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return ["manifest.json", "index.html", "style.css", "game.js"]

