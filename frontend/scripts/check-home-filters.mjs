import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const home = readFileSync(resolve(root, "src/pages/HomePage.tsx"), "utf8");
const css = readFileSync(resolve(root, "src/pages/home.css"), "utf8");

const requiredTokens = [
  "const filterOptions = [\"全部类型\", \"冒险\", \"动作\", \"策略\", \"解谜\", \"街机\", \"生存\", \"模拟\", \"竞速\", \"节奏\", \"角色扮演\", \"休闲\", \"教育\"]",
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
  "activeFeaturedGame.tags.map((tag) => (",
  "game.tags.map((tag) => (",
];

const requiredCssTokens = [
  ".home-page .search-icon",
  "font-size: 50px",
  "line-height: 1",
];

const failures = [];

if (home.includes("<span className=\"tag\">{game.tag}</span>")) {
  failures.push("Expected Home cards to render every game tag, not only the primary tag.");
}

if (home.includes("<span className=\"tag\">{activeFeaturedGame.tag}</span>")) {
  failures.push("Expected featured game to render every game tag, not only the primary tag.");
}

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
