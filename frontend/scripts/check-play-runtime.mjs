import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const playPage = readFileSync(resolve(root, "src/pages/PlayPage.tsx"), "utf8");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const playApi = readFileSync(resolve(root, "src/api/client.ts"), "utf8");

const failures = [];

const playPageTokens = [
  "createPlayEvent",
  "loadPlayManifest",
  "const [playState, setPlayState] = useState<",
  "const [manifestError, setManifestError] = useState<string | null>(null)",
  "const [iframeSrc, setIframeSrc] = useState(\"\")",
  "const [runtimeManifest, setRuntimeManifest] = useState<",
  "await loadPlayManifest(",
  "sandbox=\"allow-scripts\"",
  "onLoad={() => {",
  "onError={() => {",
  "await createPlayEvent(",
  "\"manifest_loaded\"",
  "\"started\"",
  "\"failed\"",
  "\"timeout\"",
  "\"exited\"",
  "重新加载",
  "const clearStageTimers = () => {",
  "window.clearTimeout(metaTimer);",
  "window.clearTimeout(manifestTimer);",
  "setLoadProgress((current) => Math.max(current, 28));",
  "setLoadProgress((current) => Math.max(current, 64));",
  "setLoadProgress((current) => Math.max(current, 82));",
  "setLoadProgress((current) => Math.max(current, 100));",
];

const appTokens = [
  "getGameDetail(gameId)",
  "gameError",
];

const clientTokens = [
  "credentials: \"include\"",
];

for (const token of playPageTokens) {
  if (!playPage.includes(token)) {
    failures.push(`Expected PlayPage.tsx to include: ${token}`);
  }
}

for (const token of appTokens) {
  if (!app.includes(token)) {
    failures.push(`Expected App.tsx to include: ${token}`);
  }
}

for (const token of clientTokens) {
  if (!playApi.includes(token)) {
    failures.push(`Expected client token missing: ${token}`);
  }
}

if (failures.length > 0) {
  console.error("Play runtime checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Play runtime checks passed.");
