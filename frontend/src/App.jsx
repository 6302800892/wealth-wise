import { useEffect, useState } from "react";
import Layout from "./components/Layout.jsx";
import { homeFor, parseHash, routeByName } from "./config/routes.js";
import { useSession } from "./hooks/useSession.js";
import { PAGES } from "./pages/index.js";
import LoginPage from "./pages/LoginPage.jsx";

function useHashRoute() {
  const [route, setRoute] = useState(() => parseHash(window.location.hash));
  useEffect(() => {
    const onChange = () => setRoute(parseHash(window.location.hash));
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

export default function App() {
  const route = useHashRoute();
  const { session, setSession, api } = useSession();
  const definition = routeByName(route.name);
  const allowed = session && definition && definition.role === session.role;

  useEffect(() => {
    if (!session && route.name !== "login") window.location.hash = "#/login";
    if (session && !allowed) window.location.hash = homeFor(session.role);
  }, [session, allowed, route.name]);

  const logout = async () => {
    try {
      await api.post("/api/v1/auth/logout");
    } catch {
      /* already logged out */
    }
    setSession(null);
    window.location.hash = "#/login";
  };

  if (!session || !allowed) {
    return <LoginPage api={api} onLogin={(next) => { setSession(next); window.location.hash = homeFor(next.role); }} />;
  }
  const Page = PAGES[route.name];
  return (
    <Layout session={session} current={route.name} onLogout={logout}>
      <Page api={api} session={session} params={route.params} />
    </Layout>
  );
}
