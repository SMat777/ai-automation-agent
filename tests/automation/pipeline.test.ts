/**
 * Tests for the automation pipeline and transforms.
 */

import { describe, it, expect } from "vitest";
import { Pipeline } from "../../automation/src/pipeline.js";
import { cleanData } from "../../automation/src/transforms/clean.js";

describe("Pipeline", () => {
  it("executes steps in sequence", async () => {
    const pipeline = new Pipeline("Test Pipeline");
    const result = await pipeline
      .step("Add 1", () => 1)
      .step("Double", (n) => (n as number) * 2)
      .step("Add 10", (n) => (n as number) + 10)
      .execute();

    expect(result).toBe(12);
  });

  it("passes initial input to first step", async () => {
    const pipeline = new Pipeline("Test");
    const result = await pipeline
      .step("Double", (n) => (n as number) * 2)
      .execute(5);

    expect(result).toBe(10);
  });

  it("handles async steps", async () => {
    const pipeline = new Pipeline("Async Test");
    const result = await pipeline
      .step("Async fetch", async () => {
        return Promise.resolve("data");
      })
      .step("Process", (data) => `processed: ${data}`)
      .execute();

    expect(result).toBe("processed: data");
  });

  it("returns undefined for empty pipeline", async () => {
    const pipeline = new Pipeline("Empty");
    const result = await pipeline.execute();
    expect(result).toBeUndefined();
  });
});

describe("cleanData", () => {
  it("removes null values", () => {
    const data = [{ name: "test", value: null, count: 5 }];
    const result = cleanData(data);
    expect(result[0]).not.toHaveProperty("value");
    expect(result[0]).toHaveProperty("name", "test");
    expect(result[0]).toHaveProperty("count", 5);
  });

  it("removes undefined values", () => {
    const data = [{ name: "test", value: undefined }];
    const result = cleanData(data);
    expect(result[0]).not.toHaveProperty("value");
  });

  it("trims string values", () => {
    const data = [{ name: "  hello  ", city: " Aarhus " }];
    const result = cleanData(data);
    expect(result[0]["name"]).toBe("hello");
    expect(result[0]["city"]).toBe("Aarhus");
  });

  it("preserves non-string, non-null values", () => {
    const data = [{ count: 42, active: true, tags: ["a", "b"] }];
    const result = cleanData(data);
    expect(result[0]["count"]).toBe(42);
    expect(result[0]["active"]).toBe(true);
    expect(result[0]["tags"]).toEqual(["a", "b"]);
  });

  it("handles empty array", () => {
    expect(cleanData([])).toEqual([]);
  });
});
