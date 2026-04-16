/**
 * Automation Pipeline — Entry point
 *
 * Demonstrates a multi-step data workflow:
 * Fetch → Clean → Filter → Transform → Aggregate → Format
 */

import { Pipeline } from "./pipeline.js";
import { fetchJSON } from "./connectors/api.js";
import { cleanData } from "./transforms/clean.js";
import { whereInRange } from "./transforms/filter.js";
import { selectFields, addField } from "./transforms/map.js";
import { groupBy } from "./transforms/aggregate.js";
import { toMarkdownTable, toSummary } from "./transforms/format.js";

type Record_ = Record<string, unknown>;

async function main(): Promise<void> {
  console.log("Starting automation pipeline demo\n");

  const pipeline = new Pipeline("Post Analysis Pipeline");

  const result = await pipeline
    .step("Fetch posts from API", () =>
      fetchJSON("https://jsonplaceholder.typicode.com/posts?_limit=20"),
    )
    .step("Clean data", (data) => cleanData(data as Record_[]))
    .step("Add word count field", (data) =>
      addField(data as Record_[], "wordCount", (r) =>
        typeof r["body"] === "string" ? r["body"].split(" ").length : 0,
      ),
    )
    .step("Filter posts with >20 words", (data) =>
      whereInRange(data as Record_[], "wordCount", 20, Infinity),
    )
    .step("Select relevant fields", (data) =>
      selectFields(data as Record_[], ["userId", "title", "wordCount"]),
    )
    .step("Group by user", (data) =>
      groupBy(data as Record_[], "userId", {
        totalWords: { field: "wordCount", operation: "sum" },
        avgWords: { field: "wordCount", operation: "avg" },
        postCount: { field: "wordCount", operation: "count" },
      }),
    )
    .step("Format as markdown", (data) => {
      const groups = data as Array<{
        key: string;
        count: number;
        aggregations: Record<string, number>;
      }>;
      const tableData = groups.map((g) => ({
        userId: g.key,
        posts: g.count,
        totalWords: Math.round(g.aggregations["totalWords"]),
        avgWords: Math.round(g.aggregations["avgWords"]),
      }));
      return toMarkdownTable(tableData);
    })
    .execute();

  console.log("\n--- Pipeline Result ---");
  console.log(result.output);
  console.log(`\n--- Metadata ---`);
  console.log(toSummary(result.steps as Record_[], "name"));
  console.log(`Total duration: ${result.totalDurationMs}ms`);
}

main().catch(console.error);
