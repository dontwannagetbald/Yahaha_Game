export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    retry_hint?: string | null;
  };
};

export class ApiError extends Error {
  code: string;
  retryHint: string | null;
  status: number;

  constructor(status: number, code: string, message: string, retryHint: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.retryHint = retryHint;
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function buildApiUrl(path: string): string {
  return `${apiBaseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function parseApiError(response: Response): Promise<ApiError> {
  let body: ApiErrorBody | null = null;
  try {
    body = (await response.json()) as ApiErrorBody;
  } catch {
    body = null;
  }

  const code = body?.error?.code ?? `http_${response.status}`;
  const message = body?.error?.message ?? response.statusText ?? "Request failed";
  const retryHint = body?.error?.retry_hint ?? null;
  return new ApiError(response.status, code, message, retryHint);
}

export async function requestJson<T>(
  path: string,
  init: RequestInit = {},
): Promise<T | null> {
  let response: Response;
  try {
    response = await fetch(buildApiUrl(path), {
      ...init,
      credentials: "include",
      headers: {
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new ApiError(0, "network_error", "Network error", "请检查网络连接后重试。");
  }

  if (!response.ok) {
    throw await parseApiError(response);
  }

  if (response.status === 204) {
    return null;
  }

  return (await response.json()) as T;
}
