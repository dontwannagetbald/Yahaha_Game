import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");

const required = [
  "getCurrentUser",
  "type AuthUser",
  "useEffect",
  "currentUser",
  "authBootstrapStatus",
  "getCurrentUser()",
  "setCurrentUser(response.user)",
  "setIsLoggedIn(Boolean(response.user))",
  "setAuthBootstrapStatus(\"ready\")",
  "authBootstrapStatus === \"loading\"",
  "display_name",
  "avatar_url",
];

const forbidden = [
  "aria-label=\"Bella Q 用户菜单\"",
  "<span>Bella Q</span>",
];

const failures = [];

for (const token of required) {
  if (!app.includes(token)) {
    failures.push(`Expected App.tsx to include: ${token}`);
  }
}

for (const token of forbidden) {
  if (app.includes(token)) {
    failures.push(`Expected App.tsx to remove hard-coded user token: ${token}`);
  }
}

if (failures.length > 0) {
  console.error("Current user checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Current user checks passed.");
