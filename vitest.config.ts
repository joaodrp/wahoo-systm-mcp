import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      exclude: ['node_modules/', 'dist/', 'src/test/', '**/*.test.ts'],
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
    environment: 'node',
    globals: true,
    include: ['src/test/**/*.test.ts'],
    testTimeout: 15000, // 15 seconds for tests that call external APIs
  },
});
