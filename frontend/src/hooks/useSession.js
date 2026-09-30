import { useCallback, useMemo, useState } from "react";
import { createClient } from "../api/client.js";

const KEY = "wealthwise.session";

// Session storage is a per-tab convenience only; every read/write is guarded.
function readSession() {
  try {
    const raw = window.sessionStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function writeSession(session) {
  try {
    if (session) window.sessionStorage.setItem(KEY, JSON.stringify(session));
    else window.sessionStorage.removeItem(KEY);
  } catch {
    /* storage unavailable: session lives in memory only */
  }
}

export function useSession() {
  const [session, setSession] = useState(readSession);

  const update = useCallback((next) => {
    writeSession(next);
    setSession(next);
  }, []);

  const api = useMemo(
    () =>
      createClient({
        getToken: () => (session ? session.token : null),
        onUnauthorized: () => update(null),
      }),
    [session, update],
  );

  return { session, setSession: update, api };
}
