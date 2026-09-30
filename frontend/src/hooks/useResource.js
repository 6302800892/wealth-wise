import { useCallback, useEffect, useState } from "react";

// Load data from the API and expose { data, error, loading, reload }.
export function useResource(loader, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  const reload = useCallback(async () => {
    setState((current) => ({ ...current, loading: true }));
    try {
      const data = await loader();
      setState({ data, error: null, loading: false });
    } catch (error) {
      setState({ data: null, error, loading: false });
    }
  }, deps);

  useEffect(() => {
    reload();
  }, [reload]);

  return { ...state, reload };
}

// Run a mutating API call, capturing its error for display.
export function useAction() {
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const run = useCallback(async (action) => {
    setBusy(true);
    setError(null);
    try {
      return await action();
    } catch (caught) {
      setError(caught);
      return null;
    } finally {
      setBusy(false);
    }
  }, []);

  return { run, error, busy, clearError: () => setError(null) };
}
