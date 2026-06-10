import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    include: ["__tests__/**/*.test.ts", "__tests__/**/*.test.tsx"],
    coverage: {
      provider: "v8",
      include: ["components/**/*.{ts,tsx}", "hooks/**/*.ts", "lib/**/*.ts"],
      exclude: ["**/*.d.ts", "lib/consent-schema.ts"],
      thresholds: {
        lines: 75,
        functions: 75,
        branches: 70,
        statements: 75,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
