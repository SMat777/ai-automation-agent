/**
 * Data Cleaning Transform — Removes null values, trims strings, deduplicates.
 */

type Record_ = Record<string, unknown>;

/**
 * Clean an array of records by removing null/undefined values
 * and trimming string fields.
 */
export function cleanData(data: Record_[]): Record_[] {
  return data.map((record) => {
    const cleaned: Record_ = {};

    for (const [key, value] of Object.entries(record)) {
      if (value === null || value === undefined) continue;

      if (typeof value === "string") {
        cleaned[key] = value.trim();
      } else {
        cleaned[key] = value;
      }
    }

    return cleaned;
  });
}

/**
 * Remove duplicate records based on a key field.
 */
export function deduplicate(data: Record_[], keyField: string): Record_[] {
  const seen = new Set<unknown>();
  return data.filter((record) => {
    const key = record[keyField];
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
