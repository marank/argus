import { fileURLToPath } from 'node:url'
import { mergeConfig, defineConfig, configDefaults } from 'vitest/config'
import viteConfig from './vite.config.ts'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      exclude: [...configDefaults.exclude, 'e2e/**'],
      root: fileURLToPath(new URL('./', import.meta.url)),
      coverage: {
        provider: 'v8',
        include: ['src/**'],
        exclude: ['src/main.ts', 'src/i18n/locales/**', '**/*.d.ts'],
        // A floor at today's level so coverage cannot drop; raise it as tests are
        // added, towards the 90 % the backend holds.
        thresholds: { lines: 6, statements: 6, functions: 3, branches: 4 },
      },
    },
  }),
)
