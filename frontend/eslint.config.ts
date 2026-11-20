import { globalIgnores } from 'eslint/config'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import pluginVitest from '@vitest/eslint-plugin'
import pluginOxlint from 'eslint-plugin-oxlint'
import skipFormatting from 'eslint-config-prettier/flat'

// To allow more languages other than `ts` in `.vue` files, uncomment the following lines:
// import { configureVueProject } from '@vue/eslint-config-typescript'
// configureVueProject({ scriptLangs: ['ts', 'tsx'] })
// More info at https://github.com/vuejs/eslint-config-typescript/#advanced-setup

// Import boundaries (project/* blocks below).
const rawClient = {
  group: ['@/api/client', '**/api/client'],
  importNames: ['http', 'request'],
  message: 'Call the area modules in src/api/<area>.ts.',
}
const pages = {
  group: ['@/views/*', '**/views/*'],
  message: 'Shared code must not depend on a page.',
}
// utils may still import the generated payload types (@/api/types).
const impure = {
  group: ['@/components/*', '**/components/*', '@/api/*', '!@/api/types'],
  message: 'utils stay pure: no components, no API calls.',
}

export default defineConfigWithVueTs(
  {
    name: 'app/files-to-lint',
    files: ['**/*.{vue,ts,mts,tsx}'],
  },

  globalIgnores(['**/dist/**', '**/dist-ssr/**', '**/coverage/**']),

  ...pluginVue.configs['flat/essential'],
  vueTsConfigs.recommended,

  {
    ...pluginVitest.configs.recommended,
    files: ['src/**/__tests__/*'],
  },

  ...pluginOxlint.buildFromOxlintConfigFile('.oxlintrc.json'),

  skipFormatting,

  // Limits on tangle, not on length: a long form is fine, a function with twenty branches
  // is not, and neither is shared code that reaches into a page. After the oxlint plugin,
  // which would otherwise switch these rules off.
  {
    name: 'project/readability',
    files: ['src/**/*.{ts,vue}'],
    rules: {
      // "modified": a switch counts once, so a flat dispatch over many cases is fine.
      complexity: ['error', { max: 15, variant: 'modified' }],
      'max-depth': ['error', 4],
      'no-restricted-imports': ['error', { patterns: [rawClient] }],
    },
  },
  // Later blocks replace the rule's options, so each lists every pattern that applies.
  {
    name: 'project/api',
    files: ['src/api/**', 'src/__tests__/**'],
    rules: { 'no-restricted-imports': 'off' },
  },
  {
    name: 'project/shared',
    files: ['src/components/**', 'src/composables/**', 'src/stores/**'],
    rules: { 'no-restricted-imports': ['error', { patterns: [rawClient, pages] }] },
  },
  {
    name: 'project/utils',
    files: ['src/utils/**'],
    rules: { 'no-restricted-imports': ['error', { patterns: [rawClient, pages, impure] }] },
  },
)
