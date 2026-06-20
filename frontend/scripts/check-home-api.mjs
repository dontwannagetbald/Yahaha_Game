import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const home = readFileSync(resolve(root, "src/pages/HomePage.tsx"), "utf8");
const api = readFileSync(resolve(root, "src/api/client.ts"), "utf8");

const requiredAppTokens = [
  "import { getGameDetail, likePublishedGame, listPublishedGames } from \"./api/games\"",
  "const [games, setGames] = useState<Game[]>([])",
  "const [gamesError, setGamesError] = useState<UserFacingError | null>(null)",
  "async function handleLoadGames(",
  "await listPublishedGames(",
  "setGames(response.games)",
  "async function handleLikeGame(",
  "await likePublishedGame(gameId)",
  "setAuthMode(\"login\")",
];

const requiredHomeTokens = [
  "onLoadGames",
  "onLikeGame",
  "isLoggedIn",
  "isLoading",
  "onRequireLogin",
  "useEffect(() => {",
  "void onLoadGames({",
  "sortMode === \"plays\" ? \"play_count\"",
  "q: normalizedQuery",
  "tag: selectedFilter === \"全部类型\" ? \"\" : selectedFilter",
];

const requiredApiTokens = [
  "credentials: \"include\"",
];

const failures = [];

for (const token of requiredAppTokens) {
  if (!app.includes(token)) {
    failures.push(`Expected App.tsx to include: ${token}`);
  }
}

for (const token of requiredHomeTokens) {
  if (!home.includes(token)) {
    failures.push(`Expected HomePage.tsx to include: ${token}`);
  }
}

for (const token of requiredApiTokens) {
  if (!api.includes(token)) {
    failures.push(`Expected API client token missing: ${token}`);
  }
}

if (failures.length > 0) {
  console.error("Home API checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Home API checks passed.");
