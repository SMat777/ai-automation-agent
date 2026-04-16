/**
 * Filter Transform — Remove records that don't match a predicate.
 */

type Record_ = Record<string, unknown>;

/** Filter predicate function */
export type FilterPredicate = (record: Record_) => boolean;

/**
 * Keep only records that match the predicate.
 */
export function filterRecords(data: Record_[], predicate: FilterPredicate): Record_[] {
  return data.filter(predicate);
}

/**
 * Filter records where a field equals a specific value.
 */
export function whereEquals(data: Record_[], field: string, value: unknown): Record_[] {
  return data.filter((record) => record[field] === value);
}

/**
 * Filter records where a field contains a substring (case-insensitive).
 */
export function whereContains(data: Record_[], field: string, substring: string): Record_[] {
  const lower = substring.toLowerCase();
  return data.filter((record) => {
    const val = record[field];
    return typeof val === "string" && val.toLowerCase().includes(lower);
  });
}

/**
 * Filter records where a numeric field is within a range.
 */
export function whereInRange(
  data: Record_[],
  field: string,
  min: number,
  max: number,
): Record_[] {
  return data.filter((record) => {
    const val = record[field];
    return typeof val === "number" && val >= min && val <= max;
  });
}
