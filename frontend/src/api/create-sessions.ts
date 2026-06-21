import { requestJson } from "./client";

export type CreateSessionMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  payload: Record<string, unknown> | null;
  created_at: string;
};

export type CreateSessionCard = {
  plan_id: string;
  title: string;
  introduction: string;
  tags: string[];
};

export type CreateSessionAssistantResponse = {
  message: string;
  suggestions: string[];
  card: CreateSessionCard | null;
  actions: string[];
};

export type CreateSessionUploadedAsset = {
  asset_id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  object_key: string;
  user_hint?: string | null;
};

export type CreateSessionState = {
  session_id: string;
  conversation_status: "collecting" | "ready_to_confirm" | "confirmed" | "error";
  user_requirements: Record<string, unknown>;
  game_plan: Record<string, unknown> | null;
  material_usage: {
    assets: CreateSessionUploadedAsset[];
  };
  assistant_response: CreateSessionAssistantResponse;
  messages: CreateSessionMessage[];
  handoff_to_generation?: boolean;
  created_at: string;
  updated_at: string;
};

type CreateSessionRequest = {
  initial_message?: string;
  asset_ids?: string[];
};

export type CreateSessionEventRequest = {
  type: "chat" | "upload_assets" | "regenerate" | "confirm";
  message?: string;
  uploaded_assets?: Array<CreateSessionUploadedAsset>;
  replace_existing_assets?: boolean;
  selected_plan_id?: string;
};

function normalizeCreateSession(response: CreateSessionState | null): CreateSessionState {
  if (!response) {
    throw new Error("Create session response is empty.");
  }

  return {
    ...response,
    messages: response.messages ?? [],
    material_usage: response.material_usage ?? { assets: [] },
  };
}

export async function createCreateSession(
  payload: CreateSessionRequest = {},
): Promise<CreateSessionState> {
  const response = await requestJson<CreateSessionState>("/api/create-sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  return normalizeCreateSession(response);
}

export async function getCreateSession(sessionId: string): Promise<CreateSessionState> {
  const response = await requestJson<CreateSessionState>(`/api/create-sessions/${sessionId}`);

  return normalizeCreateSession(response);
}

export async function sendCreateSessionEvent(
  sessionId: string,
  payload: CreateSessionEventRequest,
): Promise<CreateSessionState> {
  const response = await requestJson<CreateSessionState>(`/api/create-sessions/${sessionId}/events`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

  return normalizeCreateSession(response);
}
