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
  "onUploadFiles: (files: File[]) => Promise<boolean>;",
  "const nextFiles = Array.from(event.target.files ?? [])",
  "file.size > MAX_CREATE_UPLOAD_SIZE_BYTES",
  "status: \"pending\"",
  "const filesToUpload = selectedFiles.filter(",
  "const uploaded = await uploadSelectedFiles(",
  "filesToUpload.map((file) => file.file)",
  "const visibleFiles = selectedFiles;",
  "async function uploadSelectedFiles",
  "return uploaded;",
  "file.status",
  "file.error",
  "handleRetryFile",
  "retry-file-button",
  "重试",
  "remove-file-button",
  "待发送",
  "上传中",
  "上传失败",
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

if (/handleFileSelect[\s\S]*void uploadSelectedFiles\(/.test(createPage)) {
  failures.push("Expected file selection to queue attachments instead of uploading before Send.");
}

if (createPage.includes("const visibleFiles = [...boundFiles, ...selectedFiles];")) {
  failures.push("Expected composer attachments to stop showing already-bound files after send.");
}

if (createPage.includes("已绑定")) {
  failures.push("Expected sent attachments to disappear from the composer instead of showing as bound chips.");
}

if (createPage.includes("onRemoveBoundFile(file.id)")) {
  failures.push("Expected composer chips to only manage local pending files, not already-bound assets.");
}

if (failures.length > 0) {
  console.error("Create upload assets checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create upload assets checks passed.");
