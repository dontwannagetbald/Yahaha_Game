import { requestJson } from "./client";

import { getMockManifestByUrl } from "../mock/runtime";

export type PlayManifest = {
  schemaVersion?: string;
  title?: string;
  description?: string;
  entry: string;
  styles?: string[];
  scripts?: string[];
  assets?: string[];
  cover?: string;
  controls?: string[];
  runtime?: string;
  generatedAt?: string;
};

export type PlayEventType =
  | "view"
  | "manifest_loaded"
  | "started"
  | "failed"
  | "timeout"
  | "exited";

export async function loadPlayManifest(
  manifestUrl: string,
  signal?: AbortSignal,
): Promise<PlayManifest> {
  const mockManifest = getMockManifestByUrl(manifestUrl);
  if (mockManifest) {
    return mockManifest;
  }

  let response: Response;
  try {
    response = await fetch(manifestUrl, {
      method: "GET",
      cache: "no-store",
      mode: "cors",
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new Error("Manifest 加载失败，请检查资源地址或稍后重试。");
  }

  if (!response.ok) {
    throw new Error(`Manifest 加载失败（${response.status}）。`);
  }

  try {
    return (await response.json()) as PlayManifest;
  } catch {
    throw new Error("Manifest 不是有效的 JSON。");
  }
}

export function resolveIframeSrc(
  manifest: PlayManifest,
  artifactBaseUrl: string | null,
  manifestUrl: string,
): string {
  const cacheBuster = encodeURIComponent(
    manifest.generatedAt ?? `${Date.now()}`,
  );

  if (/^(https?:|data:|blob:)/.test(manifest.entry)) {
    return manifest.entry;
  }

  if (artifactBaseUrl) {
    const url = new URL(manifest.entry, artifactBaseUrl);
    url.searchParams.set("play_rev", cacheBuster);
    return url.toString();
  }

  const url = new URL(manifest.entry, manifestUrl);
  url.searchParams.set("play_rev", cacheBuster);
  return url.toString();
}

export async function createPlayEvent(
  gameId: string,
  eventType: PlayEventType,
  metadata: Record<string, unknown> = {},
): Promise<void> {
  await requestJson("/api/play-events", {
    method: "POST",
    body: JSON.stringify({
      game_id: gameId,
      event_type: eventType,
      metadata,
    }),
  });
}
