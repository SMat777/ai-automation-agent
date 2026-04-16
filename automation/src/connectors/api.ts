/**
 * API Connector — Fetches JSON data from REST endpoints.
 */

import { z } from "zod";

/** Schema for validating API responses are JSON arrays or objects */
const ApiResponseSchema = z.union([z.array(z.record(z.unknown())), z.record(z.unknown())]);

/**
 * Fetch JSON data from a URL and validate the response.
 *
 * @param url - The API endpoint to fetch from
 * @returns Parsed and validated JSON data
 * @throws Error if fetch fails or response is not valid JSON
 */
export async function fetchJSON(url: string): Promise<unknown> {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  const data: unknown = await response.json();

  // Validate that we received a JSON object or array
  const validated = ApiResponseSchema.parse(data);
  return validated;
}
