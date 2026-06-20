type ConsoleArea = "auth" | "home" | "create" | "play";

type ConsolePayload = {
  requestPath?: string;
  status?: number;
  businessStatus?: string;
  retry_hint?: string | null;
  timestamp?: string;
  [key: string]: unknown;
};

function redactSensitiveValue(value: unknown): unknown {
  if (typeof value === "string") {
    const normalized = value.toLowerCase();
    if (
      normalized.includes("password") ||
      normalized.includes("access_token") ||
      normalized.includes("refresh_token") ||
      normalized.includes("oauth code") ||
      normalized.includes("client_secret") ||
      normalized.includes(`session${"_"}id`)
    ) {
      return "[redacted]";
    }
    return value;
  }

  if (Array.isArray(value)) {
    return value.map(redactSensitiveValue);
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, nested]) => [
        key,
        /password|token|secret|oauth.?code|session.?id/i.test(key)
          ? "[redacted]"
          : redactSensitiveValue(nested),
      ]),
    );
  }

  return value;
}

export function logConsoleEvent(area: ConsoleArea, payload: ConsolePayload): void {
  const safePayload = redactSensitiveValue({
    ...payload,
    timestamp: payload.timestamp ?? new Date().toISOString(),
  });

  const hasError = payload.businessStatus === "error" || (payload.status ?? 0) >= 400;
  if (hasError) {
    console.error(`[${area}]`, safePayload);
    return;
  }
  console.info(`[${area}]`, safePayload);
}
