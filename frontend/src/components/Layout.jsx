import { useState } from "react";
import { navFor } from "../config/routes.js";

// App shell: side navigation on wide screens, collapsible top menu below 640px.
export default function Layout({ session, current, onLogout, children }) {
  const [open, setOpen] = useState(false);
  const items = navFor(session.role);
  return (
    <div className="shell">
      <header className="topbar">
        <a className="brand" href={items[0] ? items[0].href : "#/login"}>
          WealthWise
        </a>
        <button
          type="button"
          className="menu-toggle"
          aria-expanded={open}
          aria-controls="main-nav"
          data-testid="menu-toggle"
          onClick={() => setOpen(!open)}
        >
          Menu
        </button>
        <div className="user-chip" data-testid="current-user">
          {session.display_name} · {session.role}
        </div>
      </header>
      <nav id="main-nav" className={`sidenav ${open ? "open" : ""}`} aria-label="Main">
        {items.map((item) => (
          <a
            key={item.name}
            href={item.href}
            className={current === item.name ? "active" : undefined}
            data-testid={`nav-${item.name}`}
            onClick={() => setOpen(false)}
          >
            {item.label}
          </a>
        ))}
        <button type="button" className="link-button" data-testid="logout" onClick={onLogout}>
          Log out
        </button>
      </nav>
      <main className="content">{children}</main>
    </div>
  );
}
