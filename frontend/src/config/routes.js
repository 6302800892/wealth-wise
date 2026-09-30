// Hash-based routing written in-app (spec §13: no routing library).

export const ROUTES = [
  { name: "login", pattern: "/login", role: null, label: "Login" },
  { name: "dashboard", pattern: "/dashboard", role: "CUSTOMER", label: "Dashboard" },
  { name: "risk-profile", pattern: "/risk-profile", role: "CUSTOMER", label: "Risk profile" },
  { name: "goals", pattern: "/goals", role: "CUSTOMER", label: "Goals" },
  { name: "recommendation", pattern: "/recommendation", role: "CUSTOMER", label: "Recommendation" },
  { name: "holdings", pattern: "/holdings", role: "CUSTOMER", label: "Holdings" },
  { name: "rebalancing", pattern: "/rebalancing", role: "CUSTOMER", label: "Rebalancing" },
  { name: "advisor-customers", pattern: "/advisor/customers", role: "ADVISOR", label: "Customers" },
  { name: "advisor-customer", pattern: "/advisor/customers/:id", role: "ADVISOR", label: null },
  { name: "admin-templates", pattern: "/admin/templates", role: "ADMIN", label: "Templates" },
  { name: "admin-rule-sets", pattern: "/admin/rule-sets", role: "ADMIN", label: "Rule sets" },
  { name: "admin-asset-classes", pattern: "/admin/asset-classes", role: "ADMIN", label: "Asset classes" },
  { name: "admin-nav", pattern: "/admin/nav", role: "ADMIN", label: "NAV feed" },
];

const HOME = { CUSTOMER: "#/dashboard", ADVISOR: "#/advisor/customers", ADMIN: "#/admin/templates" };

function match(pattern, path) {
  const want = pattern.split("/");
  const have = path.split("/");
  if (want.length !== have.length) return null;
  const params = {};
  for (let i = 0; i < want.length; i += 1) {
    if (want[i].startsWith(":")) params[want[i].slice(1)] = decodeURIComponent(have[i]);
    else if (want[i] !== have[i]) return null;
  }
  return params;
}

export function parseHash(hash) {
  const path = (hash || "").replace(/^#/, "") || "/login";
  for (const route of ROUTES) {
    const params = match(route.pattern, path);
    if (params) return { name: route.name, params };
  }
  return { name: "login", params: {} };
}

export function routeByName(name) {
  return ROUTES.find((route) => route.name === name);
}

export function homeFor(role) {
  return HOME[role] || "#/login";
}

export function navFor(role) {
  return ROUTES.filter((route) => route.role === role && route.label).map((route) => ({
    name: route.name,
    label: route.label,
    href: `#${route.pattern}`,
    role: route.role,
  }));
}
