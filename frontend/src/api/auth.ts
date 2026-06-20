import { requestJson } from "./client";

export type AuthUser = {
  user_id: string;
  email: string | null;
  display_name: string | null;
  avatar_url: string | null;
};

export type AuthResponse = {
  authenticated?: boolean;
  user: AuthUser | null;
};

export type OAuthStartResponse = {
  authorization_url: string;
};

export type RegisterPayload = {
  email: string;
  password: string;
  display_name?: string;
  avatar_url?: string | null;
};

export type AvatarUploadDraft = {
  upload_id: string;
  object_key: string;
  upload_url: string;
  expires_in: number;
};

export type AvatarUploadResult = {
  avatar_url: string;
};

export async function getCurrentUser(): Promise<AuthResponse> {
  const response = await requestJson<AuthResponse>("/api/auth/me");
  return response ?? { authenticated: false, user: null };
}

export async function loginWithEmail(email: string, password: string): Promise<AuthResponse> {
  const response = await requestJson<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return response ?? { user: null };
}

export async function registerWithEmail(
  payload: RegisterPayload,
): Promise<AuthResponse> {
  const response = await requestJson<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return response ?? { user: null };
}

export async function logout(): Promise<void> {
  await requestJson<null>("/api/auth/logout", { method: "POST" });
}

export async function startGoogleOAuth(): Promise<OAuthStartResponse> {
  const response = await requestJson<OAuthStartResponse>("/api/auth/oauth/google/start");
  if (!response) {
    throw new Error("Google OAuth start returned an empty response.");
  }
  return response;
}

export async function presignRegistrationAvatar(file: File): Promise<AvatarUploadDraft> {
  const response = await requestJson<AvatarUploadDraft>("/api/auth/avatar/presign", {
    method: "POST",
    body: JSON.stringify({
      filename: file.name,
      mime_type: file.type,
      size_bytes: file.size,
    }),
  });
  if (!response) {
    throw new Error("Avatar upload start returned an empty response.");
  }
  return response;
}

export async function uploadAvatarBinary(uploadUrl: string, file: File): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: "PUT",
    body: file,
    headers: {
      "Content-Type": file.type || "application/octet-stream",
    },
  });
  if (!response.ok) {
    throw new Error("头像上传失败，请稍后重试。");
  }
}

export async function completeRegistrationAvatar(
  draft: AvatarUploadDraft,
  file: File,
): Promise<AvatarUploadResult> {
  const response = await requestJson<AvatarUploadResult>("/api/auth/avatar/complete", {
    method: "POST",
    body: JSON.stringify({
      upload_id: draft.upload_id,
      object_key: draft.object_key,
      filename: file.name,
      mime_type: file.type,
      size_bytes: file.size,
    }),
  });
  if (!response) {
    throw new Error("Avatar upload complete returned an empty response.");
  }
  return response;
}
