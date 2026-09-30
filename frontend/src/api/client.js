// Thin fetch wrapper: bearer token, JSON bodies and the error envelope from spec §10.1.

export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details || {};
  }
}

export function createClient({ fetchImpl = globalThis.fetch, getToken, onUnauthorized } = {}) {
  async function request(method, url, body) {
    const headers = { Accept: "application/json" };
    const token = getToken ? getToken() : null;
    if (token) headers.Authorization = `Bearer ${token}`;
    if (body !== undefined) headers["Content-Type"] = "application/json";
    const response = await fetchImpl(url, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (response.status === 204) return null;
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const error = payload && payload.error ? payload.error : {};
      if (response.status === 401 && onUnauthorized) onUnauthorized();
      throw new ApiError(response.status, error.code || "HTTP_ERROR", error.message || "Request failed", error.details);
    }
    return payload;
  }

  return {
    get: (url) => request("GET", url),
    post: (url, body) => request("POST", url, body),
    put: (url, body) => request("PUT", url, body),
    patch: (url, body) => request("PATCH", url, body),
  };
}
