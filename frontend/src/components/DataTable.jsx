// Responsive table: a normal table on wide screens, stacked cards below 640px (labels via data-label).

export default function DataTable({ columns, rows, rowKey, testId, empty = "Nothing to show yet." }) {
  if (!rows || rows.length === 0) return <p className="muted">{empty}</p>;
  return (
    <table className="data-table" data-testid={testId}>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key} className={column.numeric ? "numeric" : undefined} scope="col">
              {column.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={rowKey(row)} data-testid={`${testId}-row`}>
            {columns.map((column) => (
              <td key={column.key} data-label={column.label} className={column.numeric ? "numeric" : undefined}>
                {column.render ? column.render(row) : row[column.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
