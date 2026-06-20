import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const css = readFileSync(resolve(root, "src/styles.css"), "utf8");
const all = `${app}\n${css}`;

const required = [
  "Yahaha_Play",
  "Play worlds made by creators.",
  "更多筛选",
  "cover-tags",
  "cover-stats",
  "data-testid=\"auth-modal\"",
  "data-testid=\"create-workspace\"",
  "data-testid=\"play-stage\"",
  "退出登录",
  "avatar-button",
  "SortMode",
  "sortMode ===",
  "setSortMode",
  "filterMenuOpen",
  "setFilterMenuOpen",
  "data-testid=\"filter-menu\"",
  "aria-expanded={filterMenuOpen}",
  "全部类型",
  "selectedFilter",
  "linear-gradient(180deg, rgba(255, 255, 255, 0.12)",
  "position: fixed",
  "right: 0",
  "left: 0",
  "padding-top: 68px",
  "-webkit-backdrop-filter: saturate(140%) blur(22px)",
  "inset 0 1px 0 rgba(255, 255, 255, 0.18)",
  "♡ 14.0万",
  "46:31",
  "发癫吧，后浪！",
  "5月31日",
  "可以在这里点赞",
  "console-note",
  "□ 点赞数",
  "□ 游玩次数",
];

const failures = [];

for (const token of required) {
  const shouldBeAbsent =
    token === "可以在这里点赞" ||
    token === "console-note" ||
    token === "□ 点赞数" ||
    token === "□ 游玩次数";
  const exists = all.includes(token);
  if (shouldBeAbsent ? exists : !exists) {
    failures.push(
      shouldBeAbsent
        ? `Expected token to be absent: ${token}`
        : `Expected token to be present: ${token}`,
    );
  }
}

if (app.includes('<div className="user-area">\n          <div className="avatar"')) {
  failures.push("Guest user area must not render the default avatar before login.");
}

if (!app.includes("isLoggedIn ? (\n          <div className=\"user-area logged-in\">")) {
  failures.push("Logged-in user area must be rendered only after simulated login.");
}

if (failures.length > 0) {
  console.error("Static UI checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Static UI checks passed.");
