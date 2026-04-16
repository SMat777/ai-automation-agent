/**
 * Tests for the automation pipeline, transforms, and connector.
 */

import { describe, it, expect } from "vitest";
import { Pipeline, PipelineError } from "../../automation/src/pipeline.js";
import { cleanData, deduplicate } from "../../automation/src/transforms/clean.js";
import { filterRecords, whereEquals, whereContains, whereInRange } from "../../automation/src/transforms/filter.js";
import { selectFields, renameFields, addField } from "../../automation/src/transforms/map.js";
import { groupBy } from "../../automation/src/transforms/aggregate.js";
import { toMarkdownTable, toCSV, toSummary } from "../../automation/src/transforms/format.js";
import { ApiError } from "../../automation/src/connectors/api.js";

// ── Pipeline ────────────────────────────────────────────────────────────────

describe("Pipeline", () => {
  it("executes steps in sequence and returns structured result", async () => {
    const pipeline = new Pipeline("Test");
    const result = await pipeline
      .step("Add 1", () => 1)
      .step("Double", (n) => (n as number) * 2)
      .step("Add 10", (n) => (n as number) + 10)
      .execute();

    expect(result.output).toBe(12);
    expect(result.pipelineName).toBe("Test");
    expect(result.stepCount).toBe(3);
    expect(result.steps).toHaveLength(3);
    expect(result.totalDurationMs).toBeGreaterThanOrEqual(0);
  });

  it("passes initial input to first step", async () => {
    const result = await new Pipeline("Test")
      .step("Double", (n) => (n as number) * 2)
      .execute(5);

    expect(result.output).toBe(10);
  });

  it("handles async steps", async () => {
    const result = await new Pipeline("Async")
      .step("Async", async () => Promise.resolve("data"))
      .step("Process", (d) => `processed: ${d}`)
      .execute();

    expect(result.output).toBe("processed: data");
  });

  it("returns undefined output for empty pipeline", async () => {
    const result = await new Pipeline("Empty").execute();
    expect(result.output).toBeUndefined();
    expect(result.stepCount).toBe(0);
  });

  it("throws PipelineError on step failure", async () => {
    const pipeline = new Pipeline("Fail")
      .step("OK", () => "fine")
      .step("Boom", () => { throw new Error("kaboom"); });

    await expect(pipeline.execute()).rejects.toThrow(PipelineError);
    await expect(pipeline.execute()).rejects.toThrow('Step "Boom" failed');
  });

  it("tracks per-step duration", async () => {
    const result = await new Pipeline("Timing")
      .step("Fast", () => 1)
      .step("Fast2", () => 2)
      .execute();

    expect(result.steps[0].name).toBe("Fast");
    expect(result.steps[0].durationMs).toBeGreaterThanOrEqual(0);
  });
});

// ── Clean Transform ─────────────────────────────────────────────────────────

describe("cleanData", () => {
  it("removes null values", () => {
    const result = cleanData([{ name: "test", value: null, count: 5 }]);
    expect(result[0]).not.toHaveProperty("value");
    expect(result[0]).toHaveProperty("name", "test");
  });

  it("trims string values", () => {
    const result = cleanData([{ name: "  hello  " }]);
    expect(result[0]["name"]).toBe("hello");
  });

  it("handles empty array", () => {
    expect(cleanData([])).toEqual([]);
  });
});

describe("deduplicate", () => {
  it("removes duplicates by key field", () => {
    const data = [
      { id: 1, name: "Alice" },
      { id: 2, name: "Bob" },
      { id: 1, name: "Alice copy" },
    ];
    const result = deduplicate(data, "id");
    expect(result).toHaveLength(2);
    expect(result[0]["name"]).toBe("Alice");
  });

  it("keeps all when no duplicates", () => {
    const data = [{ id: 1 }, { id: 2 }, { id: 3 }];
    expect(deduplicate(data, "id")).toHaveLength(3);
  });
});

// ── Filter Transform ────────────────────────────────────────────────────────

describe("filterRecords", () => {
  it("filters by predicate", () => {
    const data = [{ age: 20 }, { age: 30 }, { age: 40 }];
    const result = filterRecords(data, (r) => (r["age"] as number) >= 30);
    expect(result).toHaveLength(2);
  });
});

describe("whereEquals", () => {
  it("filters by exact value", () => {
    const data = [{ status: "active" }, { status: "inactive" }, { status: "active" }];
    expect(whereEquals(data, "status", "active")).toHaveLength(2);
  });
});

describe("whereContains", () => {
  it("filters by substring case-insensitive", () => {
    const data = [{ name: "Alice Smith" }, { name: "Bob Jones" }];
    expect(whereContains(data, "name", "alice")).toHaveLength(1);
  });

  it("skips non-string fields", () => {
    const data = [{ name: 123 }];
    expect(whereContains(data, "name", "123")).toHaveLength(0);
  });
});

describe("whereInRange", () => {
  it("filters by numeric range", () => {
    const data = [{ score: 50 }, { score: 75 }, { score: 90 }];
    expect(whereInRange(data, "score", 60, 80)).toHaveLength(1);
  });

  it("includes boundary values", () => {
    const data = [{ score: 10 }, { score: 20 }];
    expect(whereInRange(data, "score", 10, 20)).toHaveLength(2);
  });
});

// ── Map Transform ───────────────────────────────────────────────────────────

describe("selectFields", () => {
  it("keeps only specified fields", () => {
    const data = [{ a: 1, b: 2, c: 3 }];
    const result = selectFields(data, ["a", "c"]);
    expect(result[0]).toEqual({ a: 1, c: 3 });
  });

  it("ignores missing fields", () => {
    const result = selectFields([{ a: 1 }], ["a", "missing"]);
    expect(result[0]).toEqual({ a: 1 });
  });
});

describe("renameFields", () => {
  it("renames specified fields", () => {
    const data = [{ old_name: "Alice", age: 30 }];
    const result = renameFields(data, { old_name: "name" });
    expect(result[0]).toEqual({ name: "Alice", age: 30 });
  });

  it("keeps unmapped fields unchanged", () => {
    const result = renameFields([{ a: 1, b: 2 }], { a: "x" });
    expect(result[0]).toEqual({ x: 1, b: 2 });
  });
});

describe("addField", () => {
  it("adds a computed field", () => {
    const data = [{ price: 100, quantity: 3 }];
    const result = addField(data, "total", (r) => (r["price"] as number) * (r["quantity"] as number));
    expect(result[0]["total"]).toBe(300);
  });

  it("preserves existing fields", () => {
    const result = addField([{ a: 1 }], "b", () => 2);
    expect(result[0]).toEqual({ a: 1, b: 2 });
  });
});

// ── Aggregate Transform ─────────────────────────────────────────────────────

describe("groupBy", () => {
  const sales = [
    { category: "A", amount: 100 },
    { category: "B", amount: 200 },
    { category: "A", amount: 150 },
    { category: "B", amount: 50 },
  ];

  it("groups by field", () => {
    const result = groupBy(sales, "category");
    expect(result).toHaveLength(2);
    expect(result[0].key).toBe("A");
    expect(result[0].count).toBe(2);
  });

  it("computes sum aggregation", () => {
    const result = groupBy(sales, "category", {
      total: { field: "amount", operation: "sum" },
    });
    const groupA = result.find((g) => g.key === "A")!;
    expect(groupA.aggregations["total"]).toBe(250);
  });

  it("computes avg aggregation", () => {
    const result = groupBy(sales, "category", {
      avg: { field: "amount", operation: "avg" },
    });
    const groupB = result.find((g) => g.key === "B")!;
    expect(groupB.aggregations["avg"]).toBe(125);
  });

  it("computes min/max", () => {
    const result = groupBy(sales, "category", {
      min: { field: "amount", operation: "min" },
      max: { field: "amount", operation: "max" },
    });
    const groupA = result.find((g) => g.key === "A")!;
    expect(groupA.aggregations["min"]).toBe(100);
    expect(groupA.aggregations["max"]).toBe(150);
  });
});

// ── Format Transform ────────────────────────────────────────────────────────

describe("toMarkdownTable", () => {
  it("formats as markdown table", () => {
    const data = [{ name: "Alice", age: 30 }];
    const table = toMarkdownTable(data);
    expect(table).toContain("| name | age |");
    expect(table).toContain("| --- | --- |");
    expect(table).toContain("| Alice | 30 |");
  });

  it("returns empty string for empty data", () => {
    expect(toMarkdownTable([])).toBe("");
  });
});

describe("toCSV", () => {
  it("formats as CSV", () => {
    const data = [{ name: "Alice", age: 30 }];
    const csv = toCSV(data);
    expect(csv).toBe("name,age\nAlice,30");
  });

  it("escapes fields with commas", () => {
    const data = [{ name: "Smith, Alice" }];
    const csv = toCSV(data);
    expect(csv).toContain('"Smith, Alice"');
  });

  it("supports custom separator", () => {
    const csv = toCSV([{ a: 1, b: 2 }], ";");
    expect(csv).toBe("a;b\n1;2");
  });
});

describe("toSummary", () => {
  it("shows record count and fields", () => {
    const data = [{ name: "Alice" }, { name: "Bob" }];
    const summary = toSummary(data);
    expect(summary).toContain("Total records: 2");
    expect(summary).toContain("Fields: name");
  });

  it("uses title field for preview", () => {
    const data = [{ title: "First" }, { title: "Second" }];
    const summary = toSummary(data, "title");
    expect(summary).toContain("First");
    expect(summary).toContain("Second");
  });
});

// ── ApiError ────────────────────────────────────────────────────────────────

describe("ApiError", () => {
  it("has correct error type", () => {
    const err = new ApiError("timeout", "timeout", undefined, true);
    expect(err.type).toBe("timeout");
    expect(err.retryable).toBe(true);
    expect(err.name).toBe("ApiError");
  });

  it("includes HTTP status", () => {
    const err = new ApiError("Not found", "http", 404);
    expect(err.status).toBe(404);
    expect(err.retryable).toBe(false);
  });
});
