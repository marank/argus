import { fileURLToPath } from 'node:url'
import { mergeConfig, defineConfig, configDefaults } from 'vitest/config'
import viteConfig from './vite.config.ts'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      // Most of the time goes into importing Vue/Naive UI and building jsdom per file;
      // VM contexts in a few threads do that ~3x faster than isolated forks, and
      // more workers only contend with each other (measured: 6 → 32 s, 23 → 109 s).
      pool: 'vmThreads',
      maxWorkers: 6,
      exclude: [...configDefaults.exclude, 'e2e/**'],
      root: fileURLToPath(new URL('./', import.meta.url)),
      coverage: {
        provider: 'v8',
        include: ['src/**'],
        exclude: ['src/main.ts', 'src/i18n/locales/**', '**/*.d.ts'],
        // A floor at today's level so coverage cannot drop; raise it as tests are
        // added, towards the 90 % the backend holds.
        thresholds: { lines: 88, statements: 86, functions: 79, branches: 82 },
      },
    },
  }),
)
