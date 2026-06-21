import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const uploadsApiPath = resolve(root, "src/api/uploads.ts");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const createPage = readFileSync(resolve(root, "src/pages/CreatePage.tsx"), "utf8");
const createSessionsApi = readFileSync(resolve(root, "src/api/create-sessions.ts"), "utf8");
const packageJson = readFileSync(resolve(root, "package.json"), "utf8");

const failures = [];

if (!existsSync(uploadsApiPath)) {
  failures.push("Expected src/api/uploads.ts to exist.");
} else {
  const uploadsApi = readFileSync(uploadsApiPath, "utf8");
  const requiredUploadApiTokens = [
    "export const MAX_CREATE_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024",
    "export async function presignUpload",
    "export async function uploadFileBinary",
    "export async function completeUpload",
    "\"/api/uploads/presign\"",
    "\"/api/uploads/complete\"",
    "method: \"PUT\"",
  ];

  for (const token of requiredUploadApiTokens) {
    if (!uploadsApi.includes(token)) {
      failures.push(`Expected uploads API to include: ${token}`);
    }
  }
}

const requiredCreateSessionsTokens = [
  "uploaded_assets?: Array<CreateSessionUploadedAsset>",
  "export type CreateSessionUploadedAsset",
  "object_key: string;",
  "replace_existing_assets?: boolean",
];

for (const token of requiredCreateSessionsTokens) {
  if (!createSessionsApi.includes(token)) {
    failures.push(`Expected create-sessions API to include: ${token}`);
  }
}

const requiredCreatePageTokens = [
  "export type CreateUploadedFileItem",
  "useState<CreateUploadedFileItem[]>([])",
  "let pendingAttachmentMessageId: string | null = null;",
  "let pendingAttachmentCreatedAt: string | null = null;",
  "if (pendingAttachments.length > 0) {",
  "role: \"user\"",
  "content: \"\"",
  "onUploadFiles: (files: File[]) => Promise<boolean>;",
  "const nextFiles = Array.from(event.target.files ?? [])",
  "file.size > MAX_CREATE_UPLOAD_SIZE_BYTES",
  "void uploadSelectedFiles(acceptedItems, acceptedFiles)",
  "async function uploadSelectedFiles",
  "file.status",
  "file.error",
  "handleRetryFile",
  "retry-file-button",
  "重试",
  "remove-file-button",
  "onRemoveBoundFile: (assetId: string) => Promise<boolean>;",
  "void onRemoveBoundFile(file.id)",
  "上传中",
  "上传失败",
  "已绑定",
  "message.content.trim().length > 0 ? (",
];

for (const token of requiredCreatePageTokens) {
  if (!createPage.includes(token)) {
    failures.push(`Expected CreatePage.tsx to include: ${token}`);
  }
}

const requiredAppTokens = [
  "MAX_CREATE_UPLOAD_SIZE_BYTES",
  "presignUpload",
  "uploadFileBinary",
  "completeUpload",
  "async function handleUploadCreateFiles(files: File[])",
  "type: \"upload_assets\"",
  "uploaded_assets: nextAssets",
  "replace_existing_assets: true",
  "material_usage.assets",
  "async function handleRemoveBoundCreateFile(assetId: string)",
  "onUploadFiles={handleUploadCreateFiles}",
  "onRemoveBoundFile={handleRemoveBoundCreateFile}",
  "create_upload_bound",
  "create_upload_failed",
];

for (const token of requiredAppTokens) {
  if (!app.includes(token)) {
    failures.push(`Expected App.tsx to include: ${token}`);
  }
}

if (!packageJson.includes("\"test:create-upload-assets\"")) {
  failures.push("Expected package.json to expose test:create-upload-assets.");
}

if (createPage.includes("useState<string[]>([])")) {
  failures.push("Expected selectedFiles to keep upload state, not only file names.");
}

if (createPage.includes("message.payload?.event_type !== \"upload_assets\"")) {
  failures.push("Expected upload_assets messages to become visible user attachment bubbles instead of being filtered out.");
}

if (failures.length > 0) {
  console.error("Create upload assets checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create upload assets checks passed.");
