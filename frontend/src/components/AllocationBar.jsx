// Stacked horizontal bar. Widths use the API's percentage strings directly (no client arithmetic).

const CLASS_COLOURS = { EQUITY: "var(--series-1)", DEBT: "var(--series-2)", GOLD: "var(--series-3)", CASH: "var(--series-4)" };

export default function AllocationBar({ items, valueKey = "target_pct", testId = "allocation-bar" }) {
  return (
    <div className="allocation">
      <div className="allocation-bar" role="img" aria-label="Allocation by asset class" data-testid={testId}>
        {items.map((item) => (
          <span
            key={item.asset_class_code}
            className="allocation-segment"
            style={{ width: `${item[valueKey]}%`, background: CLASS_COLOURS[item.asset_class_code] || "var(--series-5)" }}
            title={`${item.asset_class_code} ${item[valueKey]}%`}
          />
        ))}
      </div>
      <ul className="allocation-legend">
        {items.map((item) => (
          <li key={item.asset_class_code}>
            <span className="swatch" style={{ background: CLASS_COLOURS[item.asset_class_code] || "var(--series-5)" }} />
            {item.asset_class_name || item.asset_class_code} {item[valueKey]}%
          </li>
        ))}
      </ul>
    </div>
  );
}
