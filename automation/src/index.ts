/**
 * Automation Pipeline — Entry point
 *
 * Orchestrates multi-step data workflows by chaining
 * connectors (data sources) and transforms (data processing).
 */

import { Pipeline } from "./pipeline.js";
import { fetchJSON } from "./connectors/api.js";
import { cleanData } from "./transforms/clean.js";

async function main(): Promise<void> {
  console.log("🔄 Starting automation pipeline...\n");

  const pipeline = new Pipeline("Demo Pipeline");

  // Example: Fetch data → Clean → Output
  const result = await pipeline
    .step("Fetch sample data", () =>
      fetchJSON("https://jsonplaceholder.typicode.com/posts?_limit=5")
    )
    .step("Clean data", (data) => cleanData(data as Record<string, unknown>[]))
    .step("Transform to summary", (data) => {
      const posts = data as Array<{ title: string; body: string }>;
      return posts.map((post) => ({
        title: post.title,
        wordCount: post.body.split(" ").length,
      }));
    })
    .execute();

  console.log("\n✅ Pipeline complete!");
  console.log("Result:", JSON.stringify(result, null, 2));
}

main().catch(console.error);
