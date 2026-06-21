import { requestJson } from "./client";

import { mapChineseTagToGameTag, toUiGame, type RawGame } from "../lib/games";
import type { Game, GameSortParam } from "../types/ui";

export type GamesQuery = {
  sort: GameSortParam;
  q?: string;
  tag?: string;
};

type GamesResponse = {
  games: RawGame[];
  total: number;
};

type GameDetailResponse = RawGame;

type LikeResponse = {
  game_id: string;
  like_count: number;
  liked_by_me: boolean;
};

function buildGamesQuery(query: GamesQuery): string {
  const params = new URLSearchParams();
  params.set("sort", query.sort);

  if (query.q?.trim()) {
    params.set("q", query.q.trim());
  }

  if (query.tag?.trim()) {
    params.set("tag", mapChineseTagToGameTag(query.tag.trim()));
  }

  return params.toString();
}

export async function listPublishedGames(query: GamesQuery): Promise<{
  games: Game[];
  total: number;
}> {
  const search = buildGamesQuery(query);
  const response = await requestJson<GamesResponse>(`/api/games?${search}`);

  return {
    games: (response?.games ?? []).map(toUiGame),
    total: response?.total ?? 0,
  };
}

export async function getGameDetail(gameId: string): Promise<Game> {
  const response = await requestJson<GameDetailResponse>(`/api/games/${gameId}`);
  if (!response) {
    throw new Error("Game detail response is empty.");
  }
  return toUiGame(response);
}

export async function likePublishedGame(gameId: string): Promise<LikeResponse> {
  const response = await requestJson<LikeResponse>(`/api/games/${gameId}/like`, {
    method: "POST",
  });

  if (!response) {
    throw new Error("Like response is empty.");
  }

  return response;
}

export async function publishGame(gameId: string): Promise<Game> {
  const response = await requestJson<GameDetailResponse>(`/api/games/${gameId}/publish`, {
    method: "POST",
  });

  if (!response) {
    throw new Error("Publish response is empty.");
  }

  return toUiGame(response);
}
