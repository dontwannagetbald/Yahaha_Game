import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");

const files = {
  app: "src/App.tsx",
  mock: "src/mock/runtime.ts",
  console: "src/lib/console.ts",
  errors: "src/lib/errors.ts",
  home: "src/pages/HomePage.tsx",
  create: "src/pages/CreatePage.tsx",
  play: "src/pages/PlayPage.tsx",
  styles: "src/styles.css",
};

const contents = Object.fromEntries(
  Object.entries(files).map(([key, relativePath]) => [
    key,
    readFileSync(resolve(root, relativePath), "utf8"),
  ]),
);

const expectations = [
  [contents.app, './mock/runtime'],
  [contents.app, './lib/errors'],
  [contents.app, 'import { logConsoleEvent } from "./lib/console"'],
  [contents.app, "isMockEnabled()"],
  [contents.app, "mockAuthStore"],
  [contents.app, "authDialog"],
  [contents.app, "retry_hint"],
  [contents.app, 'const loginErrorTitle = "登录失败"'],
  [contents.app, 'const registerErrorTitle = "注册失败"'],
  [contents.app, 'const logoutErrorTitle = "退出登录失败"'],
  [contents.app, 'const googleErrorTitle = "Google 登录失败"'],
  [contents.app, 'logConsoleEvent("auth"'],
  [contents.app, 'logConsoleEvent("home"'],
  [contents.create, 'logConsoleEvent("create"'],
  [contents.play, 'logConsoleEvent("play"'],
  [contents.app, 'role="alertdialog"'],
  [contents.mock, "VITE_ENABLE_MOCK_API"],
  [contents.mock, "mockAuthStore"],
  [contents.mock, "games:"],
  [contents.mock, "tasks:"],
  [contents.console, "timestamp"],
  [contents.console, "requestPath"],
  [contents.console, "status"],
  [contents.console, "businessStatus"],
  [contents.console, "redactSensitiveValue"],
  [contents.errors, "UserFacingError"],
  [contents.errors, "retryHint"],
  [contents.errors, "nextStep"],
  [contents.styles, ".app-shell"],
  [contents.styles, "padding-top: 56px"],
  [contents.styles, ".top-nav"],
  [contents.styles, "position: fixed"],
  [contents.styles, "inset: 0 0 auto"],
  [contents.styles, "min-height: 56px"],
];

const forbidden = [
  [contents.app, "console.log(password"],
  [contents.app, "access_token"],
  [contents.app, "refresh_token"],
  [contents.console, '"session_id"'],
];

const failures = [];

if (/\.top-nav\s*\{[^}]*position:\s*sticky;/s.test(contents.styles)) {
  failures.push("Expected top-nav to avoid sticky positioning to prevent tab-restore layout shifts.");
}

for (const [source, token] of expectations) {
  if (!source.includes(token)) {
    failures.push(`Expected token missing: ${token}`);
  }
}

for (const [source, token] of forbidden) {
  if (source.includes(token)) {
    failures.push(`Forbidden token present: ${token}`);
  }
}

if (failures.length > 0) {
  console.error("App infra checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("App infra checks passed.");
