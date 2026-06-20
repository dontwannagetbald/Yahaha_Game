import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const authModal = readFileSync(resolve(root, "src/components/AuthModal.tsx"), "utf8");
const authCss = readFileSync(resolve(root, "src/components/auth-modal.css"), "utf8");

const required = [
  "loginWithEmail",
  "registerWithEmail",
  "logout as logoutRequest",
  "startGoogleOAuth",
  "authMessage",
  "authError",
  "authSubmitting",
  "authSuccessDialog",
  "handleAuthSubmit",
  "handleLogout",
  "handleGoogleLogin",
  "window.location.assign",
  "console.info(\"[auth] current user restored\"",
  "console.info(\"[auth] login success\"",
  "console.info(\"[auth] register success\"",
  "console.info(\"[auth] google oauth start\"",
  "console.info(\"[auth] logout success\"",
  "display_name?.trim()",
  "password.length < 8",
  "password !== confirmPassword",
  'navigate("/create")',
  "setAuthOpen(false)",
  'title: source === "login" ? loginSuccessTitle : registerSuccessTitle',
  'message: source === "login" ? "当前账号已成功登录。" : "当前账号已成功注册并登录。"',
  'variant="success"',
  "presentAuthFailureDialog(",
  "setAuthDialog(userError);",
  "createLoginPromptOpen",
  "创建游戏需要先登录",
  'confirmLabel="去登录"',
  "openCreateLoginModal",
];

const forbidden = [
  "onLogin={simulateLogin}",
  "session_id",
  "access_token",
  "refresh_token",
  "client_secret",
  "console.log(password",
];

const failures = [];

for (const token of required) {
  if (!app.includes(token)) {
    failures.push(`Expected App.tsx to include: ${token}`);
  }
}

const authModalRequired = [
  'type="email"',
  'type="password"',
  'autoComplete="email"',
  'autoComplete="current-password"',
  'autoComplete="new-password"',
  "disabled={authSubmitting}",
  "disabled={githubFeedbackVisible}",
  "GitHub 登录暂未启用",
  'role="alert"',
  "field-state-badge",
  "field-state-popover",
  "aria-invalid={",
  "aria-describedby={",
  "auth-subhead",
  "切换到注册",
  "切换到登录",
];

for (const token of authModalRequired) {
  if (!authModal.includes(token)) {
    failures.push(`Expected AuthModal.tsx to include: ${token}`);
  }
}

const authCssRequired = [
  "align-items: start",
  "padding: 56px 24px 24px",
  "width: min(520px, 100%)",
  "max-height: min(620px, calc(100vh - 80px))",
  "overflow-y: auto",
  ".field-state",
  ".field-state-badge",
  ".field-state-popover",
  "padding-right: 52px",
  "font-size: 32px",
  "min-height: 52px",
];

for (const token of authCssRequired) {
  if (!authCss.includes(token)) {
    failures.push(`Expected auth-modal.css to include: ${token}`);
  }
}

const authModalForbidden = [
  "avatar-upload-field",
  "avatar-upload-label",
  "avatar-upload-trigger",
  "avatar-upload-note",
];

for (const token of authModalForbidden) {
  if (authModal.includes(token)) {
    failures.push(`AuthModal.tsx should no longer include: ${token}`);
  }
}

for (const token of forbidden) {
  if (app.includes(token)) {
    failures.push(`Forbidden token in App.tsx: ${token}`);
  }
}

if (failures.length > 0) {
  console.error("Auth UI checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Auth UI checks passed.");
