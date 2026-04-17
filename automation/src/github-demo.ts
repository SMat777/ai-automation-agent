/**
 * GitHub Repository Analysis Pipeline
 *
 * Fetches public repos for a GitHub user and produces a language breakdown.
 * Fetch → Clean → Select → Filter → Aggregate → Format
 */

import { Pipeline } from "./pipeline.js";
import { fetchJSON } from "./connectors/api.js";
import { cleanData } from "./transforms/clean.js";
import { selectFields } from "./transforms/map.js";
import { filterRecords } from "./transforms/filter.js";
import { groupBy } from "./transforms/aggregate.js";
import { toMarkdownTable, toSummary } from "./transforms/format.js";

type Record_ = Record<string, unknown>;

async function main(): Promise<void> {
  console.log("Starting GitHub repository analysis pipeline\n");

  const pipeline = new Pipeline("GitHub Repo Analysis");

  const result = await pipeline
    .step("Fetch repos from GitHub API", () =>
      fetchJSON(
        "https://api.github.com/users/SMat777/repos?sort=updated&per_page=30",
      ),
    )
    .step("Clean data", (data) => cleanData(data as Record_[]))
    .step("Select relevant fields", (data) =>
      selectFields(data as Record_[], [
        "name",
        "description",
        "language",
        "stargazers_count",
        "forks_count",
        "updated_at",
      ]),
    )
    .step("Filter repos with a language", (data) =>
      filterRecords(data as Record_[], (r) => r["language"] !== null),
    )
    .step("Group by language", (data) =>
      groupBy(data as Record_[], "language", {
        repos: { field: "name", operation: "count" },
        totalStars: { field: "stargazers_count", operation: "sum" },
      }),
    )
    .step("Format as markdown", (data) => {
      const groups = data as Array<{
        key: string;
        count: number;
        aggregations: Record<string, number>;
      }>;
      const tableData = groups.map((g) => ({
        language: g.key,
        repos: g.count,
        totalStars: Math.round(g.aggregations["totalStars"]),
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
