/**
 * Map Transform — Reshape records by selecting, renaming, or computing fields.
 */

type Record_ = Record<string, unknown>;

/**
 * Select only specified fields from each record.
 */
export function selectFields(data: Record_[], fields: string[]): Record_[] {
  return data.map((record) => {
    const selected: Record_ = {};
    for (const field of fields) {
      if (field in record) {
        selected[field] = record[field];
      }
    }
    return selected;
  });
}

/**
 * Rename fields in each record.
 *
 * @param mapping - Object where keys are old names, values are new names
 */
export function renameFields(data: Record_[], mapping: Record<string, string>): Record_[] {
  return data.map((record) => {
    const renamed: Record_ = {};
    for (const [key, value] of Object.entries(record)) {
      const newKey = mapping[key] ?? key;
      renamed[newKey] = value;
    }
    return renamed;
  });
}

/**
 * Add a computed field to each record.
 *
 * @param fieldName - Name of the new field
 * @param compute - Function that takes a record and returns the computed value
 */
export function addField(
  data: Record_[],
  fieldName: string,
  compute: (record: Record_) => unknown,
): Record_[] {
  return data.map((record) => ({
    ...record,
    [fieldName]: compute(record),
  }));
}
