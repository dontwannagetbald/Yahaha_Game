import type { Game } from "../types/ui";

export type RawGameAuthor = {
  display_name: string;
};

export type RawGame = {
  id: string;
  title: string;
  description: string;
  cover_url: string | null;
  author: RawGameAuthor;
  tags: string[];
  published_at: string | null;
  play_count: number;
  like_count: number;
  liked_by_me: boolean;
  status?: "draft" | "published";
  manifest_url?: string | null;
  artifact_base_url?: string | null;
};

const fallbackCoverSvg = encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 750">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1b2228"/>
      <stop offset="55%" stop-color="#0f1112"/>
      <stop offset="100%" stop-color="#2f3b45"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="750" rx="42" fill="url(#bg)"/>
  <circle cx="240" cy="170" r="130" fill="rgba(255,194,0,0.18)"/>
  <circle cx="930" cy="520" r="180" fill="rgba(255,255,255,0.08)"/>
  <text x="96" y="650" fill="rgba(255,255,255,0.88)" font-size="56" font-family="Arial, sans-serif">Yahaha World</text>
</svg>
`);

export const fallbackCoverUrl = `data:image/svg+xml;charset=UTF-8,${fallbackCoverSvg}`;

export function formatCompactCount(value: number): string {
  if (value >= 10000) {
    return `${(value / 10000).toFixed(1)}万`;
  }

  return `${value}`;
}

export function formatLikeLabel(value: number): string {
  return `♡ ${formatCompactCount(value)}`;
}

export function formatPlayLabel(value: number): string {
  return `${formatCompactCount(value)}次游玩`;
}

export function formatPublishedAt(value: string | null): string {
  if (!value) {
    return "未发布";
  }

  const publishedAt = new Date(value);
  if (Number.isNaN(publishedAt.getTime())) {
    return "未发布";
  }

  return `${publishedAt.getMonth() + 1}月${publishedAt.getDate()}日`;
}

export function toUiGame(rawGame: RawGame): Game {
  const primaryTag = rawGame.tags[0] ?? "未分类";

  return {
    id: rawGame.id,
    title: rawGame.title,
    author: rawGame.author.display_name,
    publishedAt: formatPublishedAt(rawGame.published_at),
    publishedAtIso: rawGame.published_at,
    tag: primaryTag,
    tags: rawGame.tags.length > 0 ? rawGame.tags : [primaryTag],
    likes: formatLikeLabel(rawGame.like_count),
    likeCount: rawGame.like_count,
    likedByMe: rawGame.liked_by_me,
    plays: formatPlayLabel(rawGame.play_count),
    playCount: rawGame.play_count,
    description: rawGame.description,
    cover: rawGame.cover_url?.trim() || fallbackCoverUrl,
    status: rawGame.status ?? "published",
    manifestUrl: rawGame.manifest_url ?? null,
    artifactBaseUrl: rawGame.artifact_base_url ?? null,
  };
}

export function patchLikedGame(game: Game, likeCount: number, likedByMe: boolean): Game {
  return {
    ...game,
    likedByMe,
    likeCount,
    likes: formatLikeLabel(likeCount),
  };
}
