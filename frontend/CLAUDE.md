# frontend/ — React UI (JavaScript/JSX, Vite)

- Layout: `src/config/routes.js` (hash routes and role navigation, no router library) · `src/api/client.js` (fetch wrapper, error envelope) · `src/hooks/` (session, resources) · `src/components/` (Layout, DataTable, AllocationBar, ui) · `src/pages/{customer,advisor,admin}/`.
- **No arithmetic on financial values.** The API sends decimal strings. Display them with `src/lib/format.js` (`formatInr`, `formatPct`). The only client maths is integer basis points (`pctToBp`, `sumPct`, `capPct`) for template row sums and bar widths (KD-11).
- **Roles.** `App.jsx` redirects any route whose `role` does not match the session. The server enforces this too, so never rely on the UI alone.
- **Responsive.** Below 640px the side nav becomes a toggled menu and `DataTable` rows become labelled cards (`data-label`). Keep new tables on `DataTable` so this keeps working.
- Add a `data-testid` to anything an E2E journey needs.
- Commands: `npm test -- --run` (Vitest, `tests/unit/`), `npm run build` (served by FastAPI from `dist/`), and `npm run dev` (Vite on :5173, proxying `/api`).
- Allowed dependencies: react, react-dom, vite, @vitejs/plugin-react, vitest. Add nothing else without a spec change.
