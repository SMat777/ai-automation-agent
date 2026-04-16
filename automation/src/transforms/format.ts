/**
 * Format Transform — Convert data to different output formats.
 */

type Record_ = Record<string, unknown>;

/**
 * Convert records to a markdown table.
 */
export function toMarkdownTable(data: Record_[]): string {
  if (data.length === 0) return "";

  const headers = Object.keys(data[0]);

  const headerRow = `| ${headers.join(" | ")} |`;
  const separator = `| ${headers.map(() => "---").join(" | ")} |`;
  const rows = data.map(
    (record) => `| ${headers.map((h) => String(record[h] ?? "")).join(" | ")} |`,
  );

  return [headerRow, separator, ...rows].join("\n");
}

/**
 * Convert records to CSV format.
 */
export function toCSV(data: Record_[], separator = ","): string {
  if (data.length === 0) return "";

  const headers = Object.keys(data[0]);

  const escapeField = (value: unknown): string => {
    const str = String(value ?? "");
    if (str.includes(separator) || str.includes('"') || str.includes("\n")) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const headerLine = headers.map(escapeField).join(separator);
  const rows = data.map((record) =>
    headers.map((h) => escapeField(record[h])).join(separator),
  );

  return [headerLine, ...rows].join("\n");
}

/**
 * Convert records to a flat summary string.
 */
export function toSummary(data: Record_[], titleField?: string): string {
  const lines = [`Total records: ${data.length}`];

  if (data.length > 0) {
    const fields = Object.keys(data[0]);
    lines.push(`Fields: ${fields.join(", ")}`);

    // Show first 3 records as preview
    const preview = data.slice(0, 3);
    lines.push("", "Preview:");
    for (const record of preview) {
      const label = titleField && record[titleField]
        ? String(record[titleField])
        : JSON.stringify(record);
      lines.push(`  - ${label}`);
    }

    if (data.length > 3) {
      lines.push(`  ... and ${data.length - 3} more`);
    }
  }

  return lines.join("\n");
}
