import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const createPage = readFileSync(resolve(root, "src/pages/CreatePage.tsx"), "utf8");

const failures = [];

const requiredTokens = [
  "const [composerText, setComposerText] = useState(\"\")",
  "function handleSuggestionSelect(suggestion: string)",
  "setComposerText(suggestion)",
  "value={composerText}",
  "onChange={(event) => setComposerText(event.target.value)}",
  "assistant_response?.suggestions",
  "suggestions.map((suggestion)",
  "onClick={() => handleSuggestionSelect(suggestion)}",
];

for (const token of requiredTokens) {
  if (!createPage.includes(token)) {
    failures.push(`Expected CreatePage.tsx to include: ${token}`);
  }
}

if (createPage.includes("handleSuggestionSelect(suggestion);") && createPage.includes("onSubmit")) {
  failures.push("Expected suggestion click to fill composer text without auto-submitting.");
}

if (failures.length > 0) {
  console.error("Create suggestion checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create suggestion checks passed.");
