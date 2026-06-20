import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const home = readFileSync(resolve(root, "src/pages/HomePage.tsx"), "utf8");
const css = readFileSync(resolve(root, "src/pages/home.css"), "utf8");

const requiredTokens = [
  'const [searchDraft, setSearchDraft] = useState("")',
  'const [searchQuery, setSearchQuery] = useState("")',
  "function applySearchQuery()",
  "setSearchQuery(searchDraft)",
  "const normalizedQuery = searchQuery.trim().toLowerCase()",
  "void onLoadGames({",
  'sort: sortMode === "plays" ? "play_count" : sortMode === "likes" ? "like_count" : "latest"',
  'tag: selectedFilter === "全部类型" ? "" : selectedFilter',
  "q: normalizedQuery",
  "value={searchDraft}",
  "onBlur={applySearchQuery}",
  "if (event.key === \"Enter\")",
  "setSearchDraft(event.target.value)",
  "const activeFeaturedGame = useMemo(() => featuredGame ?? games[0] ?? null, [featuredGame, games])",
  "card-like-button",
  "onLikeGame(game.id)",
  "onRequireLogin()",
];

const requiredCssTokens = [
  ".home-page .search-icon",
  "font-size: 50px",
  "line-height: 1",
];

const failures = [];

for (const token of requiredTokens) {
  if (!home.includes(token)) {
    failures.push(`Expected HomePage token missing: ${token}`);
  }
}

for (const token of requiredCssTokens) {
  if (!css.includes(token)) {
    failures.push(`Expected home.css token missing: ${token}`);
  }
}

if (failures.length > 0) {
  console.error("Home filter checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Home filter checks passed.");
