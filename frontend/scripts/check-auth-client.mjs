import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");

const files = [
  "src/api/client.ts",
  "src/api/auth.ts",
  "vite.config.ts",
];

const requiredByFile = new Map([
  [
    "src/api/client.ts",
    [
      "import.meta.env.VITE_API_BASE_URL",
      "rawApiBaseUrl",
      "if (!apiBaseUrl)",
      "credentials: \"include\"",
      "ApiError",
      "parseApiError",
      "requestJson",
      "status === 204",
      "Network error",
      "retry_hint",
    ],
  ],
  [
    "src/api/auth.ts",
    [
      "getCurrentUser",
      "loginWithEmail",
      "registerWithEmail",
      "logout",
      "startGoogleOAuth",
      "/api/auth/me",
      "/api/auth/login",
      "/api/auth/register",
      "/api/auth/logout",
      "/api/auth/oauth/google/start",
    ],
  ],
  [
    "vite.config.ts",
    [
      'envDir: ".."',
      "loadEnv",
      "VITE_API_PROXY_TARGET",
      "apiProxyTarget",
      '"/api"',
      "target: apiProxyTarget",
      "changeOrigin: true",
    ],
  ],
]);

const forbidden = [
  "console.log(password",
  "console.info(password",
  "console.error(password",
  "session_id",
  "access_token",
  "refresh_token",
  "client_secret",
];

const failures = [];

for (const file of files) {
  let source = "";
  try {
    source = readFileSync(resolve(root, file), "utf8");
  } catch {
    failures.push(`Expected file to exist: ${file}`);
    continue;
  }

  for (const token of requiredByFile.get(file) ?? []) {
    if (!source.includes(token)) {
      failures.push(`Expected ${file} to include: ${token}`);
    }
  }

  for (const token of forbidden) {
    if (source.includes(token)) {
      failures.push(`Forbidden sensitive token in ${file}: ${token}`);
    }
  }
}

if (failures.length > 0) {
  console.error("Auth client checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Auth client checks passed.");
