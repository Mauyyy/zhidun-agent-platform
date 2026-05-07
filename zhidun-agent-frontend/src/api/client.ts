import { apiUrl } from '@/config/env';
import type { ApiEnvelope } from '@/types/api';

export class ApiError extends Error {
  status: number;
  body?: unknown;

  constructor(message: string, status: number, body?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('access_token');
  if (token) return { Authorization: `Bearer ${token}` };
  return {};
}

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!text) return undefined as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError('响应不是合法 JSON', res.status, text);
  }
}

/**
 * 统一请求。后端若返回 { code, data, message }，在此解包 data。
 * 若后端直接返回裸 JSON，可把 skipEnvelope 设为 true 或让后端与 ApiEnvelope 对齐。
 */
export async function request<T>(
  path: string,
  options: RequestInit & { skipEnvelope?: boolean } = {}
): Promise<T> {
  const { skipEnvelope, ...init } = options;
  const url = apiUrl(path);
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...(init.headers || {}),
  };

  const res = await fetch(url, { ...init, headers });

  if (!res.ok) {
    const errBody = await parseJson<unknown>(res).catch(() => undefined);
    const msg =
      errBody && typeof errBody === 'object' && 'message' in errBody
        ? String((errBody as { message: unknown }).message)
        : res.statusText;
    throw new ApiError(msg || `HTTP ${res.status}`, res.status, errBody);
  }

  const raw = await parseJson<ApiEnvelope<T> | T>(res);

  if (skipEnvelope) {
    return raw as T;
  }

  if (raw && typeof raw === 'object' && 'data' in raw && 'code' in raw) {
    const env = raw as ApiEnvelope<T>;
    if (env.code !== 0 && env.code !== 200) {
      throw new ApiError(env.message || '业务错误', env.code, env);
    }
    return env.data;
  }

  return raw as T;
}
