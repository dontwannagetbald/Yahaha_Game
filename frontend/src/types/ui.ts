export type Page = "home" | "create" | "play";
export type AuthMode = "login" | "register";
export type SortMode = "plays" | "likes" | "latest";
export type GameSortParam = "play_count" | "like_count" | "latest";

export type Game = {
  id: string;
  title: string;
  author: string;
  publishedAt: string;
  publishedAtIso: string | null;
  tag: string;
  tags: string[];
  likes: string;
  likeCount: number;
  likedByMe: boolean;
  plays: string;
  playCount: number;
  description: string;
  cover: string;
  status: "draft" | "published";
  manifestUrl: string | null;
  artifactBaseUrl: string | null;
};
