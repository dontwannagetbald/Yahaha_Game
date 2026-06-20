import { ApiError } from "../api/client";

export type UserFacingError = {
  title: string;
  message: string;
  retryHint: string | null;
  nextStep: string;
};

export function createUserError(
  title: string,
  error: unknown,
  nextStep: string,
): UserFacingError {
  if (error instanceof ApiError) {
    return {
      title,
      message: error.message,
      retryHint: error.retryHint,
      nextStep,
    };
  }

  if (error instanceof Error) {
    return {
      title,
      message: error.message,
      retryHint: null,
      nextStep,
    };
  }

  return {
    title,
    message: "发生未知错误，请稍后重试。",
    retryHint: null,
    nextStep,
  };
}
