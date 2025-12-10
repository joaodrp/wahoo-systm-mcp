import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/test/**/*.test.ts'],
    testTimeout: 15000, // 15 seconds for tests that call external APIs
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'build/',
        'src/test/',
        '**/*.test.ts'
      ]
    }
  }
});
