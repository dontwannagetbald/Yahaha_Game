import { requestJson } from "./client";

export const MAX_CREATE_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024;

export type UploadDraft = {
  upload_id: string;
  object_key: string;
  upload_url: string;
  expires_in: number;
};

export type UploadedAsset = {
  asset_id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  object_key?: string;
};

export async function presignUpload(file: File): Promise<UploadDraft> {
  const response = await requestJson<UploadDraft>("/api/uploads/presign", {
    method: "POST",
    body: JSON.stringify({
      filename: file.name,
      mime_type: file.type || "application/octet-stream",
      size_bytes: file.size,
    }),
  });
  if (!response) {
    throw new Error("Upload presign returned an empty response.");
  }
  return response;
}

export async function uploadFileBinary(uploadUrl: string, file: File): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: "PUT",
    body: file,
    headers: {
      "Content-Type": file.type || "application/octet-stream",
    },
  });
  if (!response.ok) {
    throw new Error("文件上传失败，请稍后重试。");
  }
}

export async function completeUpload(draft: UploadDraft, file: File): Promise<UploadedAsset> {
  const response = await requestJson<UploadedAsset>("/api/uploads/complete", {
    method: "POST",
    body: JSON.stringify({
      upload_id: draft.upload_id,
      object_key: draft.object_key,
      filename: file.name,
      mime_type: file.type || "application/octet-stream",
      size_bytes: file.size,
    }),
  });
  if (!response) {
    throw new Error("Upload complete returned an empty response.");
  }
  return {
    ...response,
    object_key: response.object_key ?? draft.object_key,
  };
}
