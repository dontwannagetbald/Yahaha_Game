export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    retry_hint?: string | null;
    details?: unknown;
  };
  detail?:
    | string
    | Array<{
        type?: string;
        loc?: Array<string | number>;
        msg?: string;
      }>
    | {
        code?: string;
        message?: string;
        retry_hint?: string | null;
        details?: unknown;
      };
};

export class ApiError extends Error {
  code: string;
  details?: string;
  retryHint: string | null;
  status: number;

  constructor(
    status: number,
    code: string,
    message: string,
    retryHint: string | null = null,
    details?: string,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.retryHint = retryHint;
    this.details = details;
  }
}

const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
const apiBaseUrl = rawApiBaseUrl.replace(/\/$/, "");

function stringifyErrorDetails(value: unknown): string | undefined {
  if (value == null) {
    return undefined;
  }
  if (typeof value === "string") {
    return value;
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function normalizeErrorDetail(body: ApiErrorBody | null): {
  code?: string;
  details?: string;
  message?: string;
  retryHint: string | null;
} {
  if (!body?.detail) {
    return { retryHint: null };
  }

  if (typeof body.detail === "string") {
    return { message: body.detail, retryHint: null };
  }

  if (Array.isArray(body.detail)) {
    const firstDetail = body.detail[0];
    const detailMessage =
      typeof firstDetail?.msg === "string" && firstDetail.msg.trim().length > 0
        ? firstDetail.msg
        : null;

    if (!detailMessage) {
      return { retryHint: null };
    }

    return {
      code: "validation_error",
      message: detailMessage,
      retryHint: null,
    };
  }

  return {
    code: body.detail.code,
    details: stringifyErrorDetails(body.detail.details),
    message: body.detail.message,
    retryHint: body.detail.retry_hint ?? null,
  };
}

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (!apiBaseUrl) {
    return normalizedPath;
  }
  return `${apiBaseUrl}${normalizedPath}`;
}

export async function parseApiError(response: Response): Promise<ApiError> {
  let body: ApiErrorBody | null = null;
  try {
    body = (await response.json()) as ApiErrorBody;
  } catch {
    body = null;
  }

  const detail = normalizeErrorDetail(body);
  const code = body?.error?.code ?? detail.code ?? `http_${response.status}`;
  const message = body?.error?.message ?? detail.message ?? response.statusText ?? "Request failed";
  const retryHint = body?.error?.retry_hint ?? detail.retryHint;
  const details = stringifyErrorDetails(body?.error?.details) ?? detail.details;
  return new ApiError(response.status, code, message, retryHint, details);
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
