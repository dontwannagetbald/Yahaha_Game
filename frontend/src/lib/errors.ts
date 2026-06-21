import { ApiError } from "../api/client";

export type UserFacingError = {
  title: string;
  message: string;
  retryHint: string | null;
  nextStep: string;
  details?: string;
};

export function createUserError(
  title: string,
  error: unknown,
  nextStep: string,
): UserFacingError {
  if (error instanceof ApiError) {
    const normalizedApiMessage =
      error.status === 422 && error.message === "Unprocessable Entity"
        ? "当前请求暂时无法处理，请检查输入内容后再试。"
        : error.message;
    return {
      title,
      message: normalizedApiMessage,
      retryHint: error.retryHint,
      nextStep,
      details: error.details,
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
