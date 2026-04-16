/**
 * Data Cleaning Transform — Removes null values and normalizes data.
 */

/**
 * Clean an array of records by removing null/undefined values
 * and trimming string fields.
 *
 * @param data - Array of records to clean
 * @returns Cleaned records
 */
export function cleanData(
  data: Record<string, unknown>[]
): Record<string, unknown>[] {
  return data.map((record) => {
    const cleaned: Record<string, unknown> = {};

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
