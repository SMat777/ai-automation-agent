/**
 * Aggregate Transform — Group records and compute summary statistics.
 */

type Record_ = Record<string, unknown>;

/** Aggregation result for a single group */
export interface GroupResult {
  key: string;
  count: number;
  records: Record_[];
  aggregations: Record<string, number>;
}

/**
 * Group records by a field and compute aggregations.
 *
 * @param data - Array of records to group
 * @param groupField - Field to group by
 * @param aggregations - Object mapping output names to {field, operation} pairs
 *
 * @example
 * ```ts
 * groupBy(sales, "category", {
 *   totalRevenue: { field: "amount", operation: "sum" },
 *   avgPrice: { field: "price", operation: "avg" },
 * })
 * ```
 */
export function groupBy(
  data: Record_[],
  groupField: string,
  aggregations?: Record<string, { field: string; operation: "sum" | "avg" | "min" | "max" | "count" }>,
): GroupResult[] {
  // Group records
  const groups = new Map<string, Record_[]>();

  for (const record of data) {
    const key = String(record[groupField] ?? "undefined");
    const group = groups.get(key) ?? [];
    group.push(record);
    groups.set(key, group);
  }

  // Compute aggregations per group
  return Array.from(groups.entries()).map(([key, records]) => {
    const aggs: Record<string, number> = {};

    if (aggregations) {
      for (const [name, { field, operation }] of Object.entries(aggregations)) {
        const values = records
          .map((r) => r[field])
          .filter((v): v is number => typeof v === "number");

        aggs[name] = computeAggregation(values, operation);
      }
    }

    return { key, count: records.length, records, aggregations: aggs };
  });
}

function computeAggregation(
  values: number[],
  operation: "sum" | "avg" | "min" | "max" | "count",
): number {
  if (values.length === 0) return 0;

  switch (operation) {
    case "sum":
      return values.reduce((a, b) => a + b, 0);
    case "avg":
      return values.reduce((a, b) => a + b, 0) / values.length;
    case "min":
      return Math.min(...values);
    case "max":
      return Math.max(...values);
    case "count":
      return values.length;
  }
}
