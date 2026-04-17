import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["../tests/automation/**/*.test.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "text-summary", "lcov"],
      include: ["src/**/*.ts"],
      exclude: ["src/index.ts"],
    },
  },
});
