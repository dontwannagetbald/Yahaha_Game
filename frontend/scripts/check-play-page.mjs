import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const play = readFileSync(resolve(root, "src/pages/PlayPage.tsx"), "utf8");
const playCss = readFileSync(resolve(root, "src/pages/play.css"), "utf8");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const gamesLib = readFileSync(resolve(root, "src/lib/games.ts"), "utf8");
const descriptionIndex = play.indexOf('<p className="play-description">');
const controlsSectionIndex = play.indexOf('<section className="play-controls-section"');
const tagRowIndex = play.indexOf('<div className="tag-row">');

const requiredPlayTokens = [
  "const relatedGames = games.filter(",
  "candidate.tag === game.tag",
  "candidate.id !== game.id",
  "game.likedByMe",
  'const [loadProgress, setLoadProgress] = useState(0)',
  'const [playState, setPlayState] = useState<',
  "loading-overlay",
  "loading-progress-fill",
  "loading-progress-value",
  "style={{ width: `${loadProgress}%` }}",
  "runtimeManifest?.controls?.length",
  "play-controls-section",
  "play-controls-list",
  "void onLikeGame(game.id)",
  "like-button",
  "more-games-section",
  "more-games-grid",
  "more-game-card",
  "onOpenGame(relatedGame)",
];

const requiredAppTokens = [
  "async function handleLikeGame(gameId: string)",
  "patchLikedGame(game, response.like_count, response.liked_by_me)",
  "getGameDetail(gameId)",
  "onLikeGame={handleLikeGame}",
  "onOpenGame={openPlay}",
];

const requiredGamesLibTokens = [
  "const GAME_TAG_LABELS",
  "survival:",
  "arcade:",
  "puzzle:",
  "action:",
  "casual:",
  "simulation:",
  "racing:",
  "adventure:",
  "strategy:",
  "rhythm:",
  "roleplay:",
  "educational:",
  "mapGameTagToChinese",
];

const requiredCssTokens = [
  ".play-page .like-button",
  ".play-page .like-button.active",
  ".play-page .more-games-section",
  ".play-page .more-games-grid",
  ".play-page .more-game-card",
  ".play-page .loading-overlay",
  ".play-page .loading-cover",
  ".play-page .loading-progress-track",
  ".play-page .loading-progress-fill",
  ".play-page .play-controls-section",
  ".play-page .play-controls-list",
  "overflow-y: auto",
];

const failures = [];

for (const token of requiredPlayTokens) {
  if (!play.includes(token)) {
    failures.push(`Expected PlayPage.tsx to include: ${token}`);
  }
}

for (const token of requiredAppTokens) {
  if (!app.includes(token)) {
    failures.push(`Expected App.tsx to include: ${token}`);
  }
}

for (const token of requiredGamesLibTokens) {
  if (!gamesLib.includes(token)) {
    failures.push(`Expected games.ts to include: ${token}`);
  }
}

for (const token of requiredCssTokens) {
  if (!playCss.includes(token)) {
    failures.push(`Expected play.css to include: ${token}`);
  }
}

if (failures.length > 0) {
  console.error("Play page checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

if (
  descriptionIndex === -1 ||
  controlsSectionIndex === -1 ||
  tagRowIndex === -1 ||
  controlsSectionIndex < descriptionIndex ||
  tagRowIndex < controlsSectionIndex
) {
  console.error("Play page checks failed:");
  console.error("- Expected play-description, play-controls-section, then tag-row in PlayPage.tsx");
  process.exit(1);
}

console.info("Play page checks passed.");
