/** 请求基址：生产可设为 https://api.example.com；开发留空则走同源 + Vite 代理 */
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

/** 与后端约定的前缀，如 /api/v1 */
export const API_PREFIX = import.meta.env.VITE_API_PREFIX ?? '/api/v1';

/** 为 true 时不发网络请求，使用 src/api/mock 数据（默认开发联调前为 true） */
export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

/**
 * 实时联动模式：
 * - auto: 后端可用时优先推送，失败后自动降级轮询
 * - push: 强制推送（SSE）
 * - poll: 强制轮询
 */
export const SECURITY_REALTIME_MODE =
  (import.meta.env.VITE_SECURITY_REALTIME_MODE as 'auto' | 'push' | 'poll' | undefined) ?? 'auto';

/** 轮询间隔（毫秒） */
export const SECURITY_POLL_INTERVAL_MS = Number(import.meta.env.VITE_SECURITY_POLL_INTERVAL_MS ?? 5000);

export function apiUrl(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${API_PREFIX}${p}`;
}
