import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const files = {
  games: readFileSync(resolve(root, "src/api/games.ts"), "utf8"),
  app: readFileSync(resolve(root, "src/App.tsx"), "utf8"),
  createPage: readFileSync(resolve(root, "src/pages/CreatePage.tsx"), "utf8"),
};

const expectations = [
  [files.games, "export async function publishGame(gameId: string): Promise<Game>"],
  [files.games, "`/api/games/${gameId}/publish`"],
  [files.app, "publishGame"],
  [files.app, "const [publishingGameId, setPublishingGameId]"],
  [files.app, "async function handlePublishCreateGame"],
  [files.app, "await publishGame(task.game_id)"],
  [files.app, "await handleLoadGames({ sort: \"latest\", q: \"\", tag: \"\" })"],
  [files.app, "navigate(\"/\")"],
  [files.app, "Publish 成功"],
  [files.createPage, "onPublishGame: (task: CreateTaskItem) => Promise<boolean>;"],
  [files.createPage, "publishingGameId: string | null;"],
  [files.createPage, "selectedTask ? onPublishGame(selectedTask) : Promise.resolve(false)"],
  [files.createPage, "publishingGameId === selectedTaskGameId"],
];

const failures = expectations.filter(([contents, token]) => !contents.includes(token));

if (failures.length > 0) {
  console.error("Create publish checks failed:");
  for (const [, token] of failures) {
    console.error(`- Expected token missing: ${token}`);
  }
  process.exit(1);
}

console.info("Create publish checks passed.");
