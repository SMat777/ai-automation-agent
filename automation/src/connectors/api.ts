/**
 * API Connector — Fetches JSON data from REST endpoints
 * with retry logic, error classification, and response validation.
 */

import { z } from "zod";

/** Configuration for API requests */
export interface ConnectorConfig {
  /** Maximum number of retry attempts (default: 3) */
  maxRetries?: number;
  /** Base delay in ms for exponential backoff (default: 1000) */
  baseDelay?: number;
  /** Request timeout in ms (default: 10000) */
  timeout?: number;
  /** Custom headers to include */
  headers?: Record<string, string>;
}

const DEFAULT_CONFIG: Required<ConnectorConfig> = {
  maxRetries: 3,
  baseDelay: 1000,
  timeout: 10000,
  headers: {},
};

/** Structured error types for API failures */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly type: "network" | "http" | "parse" | "validation" | "timeout",
    public readonly status?: number,
    public readonly retryable: boolean = false,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Schema for validating API responses */
const ApiResponseSchema = z.union([
  z.array(z.record(z.unknown())),
  z.record(z.unknown()),
]);

/**
 * Fetch JSON from a URL with retry, timeout, and validation.
 *
 * @param url - The API endpoint to fetch from
 * @param config - Optional connector configuration
 * @returns Parsed and validated JSON data
 * @throws ApiError with classified error type
 */
export async function fetchJSON(
  url: string,
  config?: ConnectorConfig,
): Promise<unknown> {
  const cfg = { ...DEFAULT_CONFIG, ...config };

  let lastError: ApiError | null = null;

  for (let attempt = 1; attempt <= cfg.maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), cfg.timeout);

      const response = await fetch(url, {
        headers: cfg.headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const retryable = response.status >= 500 || response.status === 429;
        throw new ApiError(
          `HTTP ${response.status}: ${response.statusText}`,
          "http",
          response.status,
          retryable,
        );
      }

      const data: unknown = await response.json();
      return ApiResponseSchema.parse(data);
    } catch (error) {
      if (error instanceof ApiError) {
        lastError = error;
      } else if (error instanceof z.ZodError) {
        // Validation errors are not retryable
        throw new ApiError(
          `Response validation failed: ${error.message}`,
          "validation",
        );
      } else if (error instanceof DOMException && error.name === "AbortError") {
        lastError = new ApiError(
          `Request timed out after ${cfg.timeout}ms`,
          "timeout",
          undefined,
          true,
        );
      } else {
        lastError = new ApiError(
          `Network error: ${error instanceof Error ? error.message : String(error)}`,
          "network",
          undefined,
          true,
        );
      }

      if (!lastError.retryable || attempt === cfg.maxRetries) {
        throw lastError;
      }

      const delay = cfg.baseDelay * Math.pow(2, attempt - 1);
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

/**
 * Fetch all pages from a paginated API endpoint.
 * Supports offset-based pagination (page/per_page query params).
 *
 * @param baseUrl - API endpoint (without pagination params)
 * @param config - Optional connector configuration
 * @param pageSize - Records per page (default: 20)
 * @param maxPages - Safety limit (default: 10)
 * @returns Combined array of all records
 */
export async function fetchAllPages(
  baseUrl: string,
  config?: ConnectorConfig,
  pageSize = 20,
  maxPages = 10,
): Promise<Record<string, unknown>[]> {
  const allRecords: Record<string, unknown>[] = [];
  const separator = baseUrl.includes("?") ? "&" : "?";

  for (let page = 1; page <= maxPages; page++) {
    const url = `${baseUrl}${separator}_page=${page}&_limit=${pageSize}`;
    const data = await fetchJSON(url, config);

    if (!Array.isArray(data) || data.length === 0) break;

    allRecords.push(...(data as Record<string, unknown>[]));

    if (data.length < pageSize) break; // Last page
  }

  return allRecords;
}
