import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");

const expectedFiles = [
  "src/pages/HomePage.tsx",
  "src/pages/CreatePage.tsx",
  "src/pages/PlayPage.tsx",
  "src/pages/home.css",
  "src/pages/create.css",
  "src/pages/play.css",
  "src/components/AuthModal.tsx",
  "src/components/auth-modal.css",
  "src/components/TopNav.tsx",
];

const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const main = readFileSync(resolve(root, "src/main.tsx"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const stylesCss = readFileSync(resolve(root, "src/styles.css"), "utf8");
const playCss = readFileSync(resolve(root, "src/pages/play.css"), "utf8");

const failures = [];

for (const file of expectedFiles) {
  if (!existsSync(resolve(root, file))) {
    failures.push(`Expected file to exist: ${file}`);
  }
}

const expectations = [
  [pkg, '"react-router-dom"'],
  [main, "BrowserRouter"],
  [app, "Routes"],
  [app, "Route"],
  [app, 'path="/"'],
  [app, 'path="/create"'],
  [app, 'path="/play/:gameId"'],
  [app, "HomePage"],
  [app, "CreatePage"],
  [app, "PlayPage"],
  [app, 'navigate("/create")'],
  [app, "useNavigate"],
  [app, "useLocation"],
  [app, "showTopNav"],
  [app, 'className={showTopNav ? "app-shell" : "play-shell"}'],
];

for (const [source, token] of expectations) {
  if (!source.includes(token)) {
    failures.push(`Expected token missing: ${token}`);
  }
}

if (app.includes("function HomePage(")) {
  failures.push("HomePage should be extracted from App.tsx");
}

if (app.includes("function CreatePage(")) {
  failures.push("CreatePage should be extracted from App.tsx");
}

if (app.includes("function PlayPage(")) {
  failures.push("PlayPage should be extracted from App.tsx");
}

if (app.includes("function AuthModal(")) {
  failures.push("AuthModal should be extracted from App.tsx");
}

if (!/\.top-nav\s*\{[^}]*position:\s*sticky;[^}]*top:\s*0;[^}]*\}/s.test(stylesCss)) {
  failures.push("Expected top nav to stay in normal layout flow with sticky positioning to avoid route tab layout jumps.");
}

if (/\.app-shell\s*\{[^}]*padding-top:\s*56px;[^}]*\}/s.test(stylesCss)) {
  failures.push("Expected app-shell to avoid fixed-nav padding compensation that causes tab-switch layout jumps.");
}

const playCssExpectations = [
  ".play-shell",
  "padding-top: 0",
  ".play-page.play-layout",
  "height: 100vh",
  "overflow: hidden",
  ".play-stage-wrap",
  "min-height: 0",
  ".play-stage",
  "height: 100%",
];

for (const token of playCssExpectations) {
  if (!playCss.includes(token)) {
    failures.push(`Expected play.css to include: ${token}`);
  }
}

if (failures.length > 0) {
  console.error("Routing structure checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Routing structure checks passed.");
