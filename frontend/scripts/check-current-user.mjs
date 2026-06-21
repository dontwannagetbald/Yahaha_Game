import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const topNav = readFileSync(resolve(root, "src/components/TopNav.tsx"), "utf8");
const css = readFileSync(resolve(root, "src/styles.css"), "utf8");

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

const requiredTopNav = [
  "useEffect",
  "useRef",
  "useState",
  "const USER_MENU_CLOSE_DELAY_MS = 180;",
  "function getUserAvatarInitial(user: AuthUser | null): string",
  "user?.display_name?.trim()",
  "user?.email?.split(\"@\", 1)[0]?.trim()",
  "{getUserAvatarInitial(currentUser)}",
  "const [userMenuOpen, setUserMenuOpen] = useState(false);",
  "const closeTimerRef = useRef<number | null>(null);",
  "window.setTimeout",
  "window.clearTimeout",
  "onMouseEnter={handleOpenUserMenu}",
  "onMouseLeave={scheduleCloseUserMenu}",
  "onFocus={handleOpenUserMenu}",
  "onBlur={scheduleCloseUserMenu}",
  "user-area logged-in",
  "menu-open",
  "aria-expanded={userMenuOpen}",
];

const requiredCss = [
  "linear-gradient(135deg, rgba(184, 109, 255, 0.16) 0%, rgba(124, 92, 255, 0.16) 52%, rgba(236, 140, 255, 0.16) 100%)",
  "color: #ffffff",
  "font-weight: 800",
  ".user-area.menu-open .user-menu",
];

const forbidden = [
  "aria-label=\"Bella Q 用户菜单\"",
  "<span>Bella Q</span>",
  "#6f4bc8",
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

if (css.includes("#6f4bc8")) {
  failures.push("Expected default user avatar CSS to avoid an opaque purple fallback");
}

for (const token of requiredTopNav) {
  if (!topNav.includes(token)) {
    failures.push(`Expected TopNav.tsx to include: ${token}`);
  }
}

for (const token of requiredCss) {
  if (!css.includes(token)) {
    failures.push(`Expected styles.css to include: ${token}`);
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
