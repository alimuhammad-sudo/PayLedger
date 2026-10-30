// Every call goes to /api on this app's own origin (proxied to the backend), with the
// httpOnly session cookie sent automatically. Nothing here ever sees the token.

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public fields: Record<string, string> = {},
  ) {
    super(message);
  }
}

type Query = Record<string, string | number | boolean | null | undefined>;

export function toQuery(params: Query = {}): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

/** Turn any error body into ApiError: ours ({message, fields}) or FastAPI's ({detail}). */
export function toApiError(status: number, body: unknown): ApiError {
  const b = (body ?? {}) as { message?: string; fields?: Record<string, string>; detail?: unknown };
  if (Array.isArray(b.detail)) {
    const fields: Record<string, string> = {};
    for (const d of b.detail as { loc?: unknown[]; msg?: string }[]) {
      const loc = d.loc ?? [];
      fields[String(loc[loc.length - 1] ?? "request")] = d.msg ?? "is invalid";
    }
    return new ApiError(status, "Please fix the highlighted fields", fields);
  }
  const fallback = status === 0 ? "Cannot reach the server." : `Request failed (${status}).`;
  return new ApiError(status, b.message ?? fallback, b.fields ?? {});
}

export async function api<T>(
  path: string,
  init: { method?: string; body?: unknown; query?: Query } = {},
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}${toQuery(init.query)}`, {
      method: init.method ?? "GET",
      credentials: "same-origin",
      headers: init.body === undefined ? undefined : { "Content-Type": "application/json" },
      body: init.body === undefined ? undefined : JSON.stringify(init.body),
    });
  } catch {
    throw toApiError(0, null);
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => null);
  if (!res.ok) throw toApiError(res.status, body);
  return body as T;
}
