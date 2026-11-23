import { globalIgnores } from 'eslint/config'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import pluginVitest from '@vitest/eslint-plugin'
import pluginOxlint from 'eslint-plugin-oxlint'
import pluginComments from '@eslint-community/eslint-plugin-eslint-comments/configs'
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
  // Tests test: every test asserts, and none is focused or skipped and forgotten.
  {
    name: 'project/tests',
    files: ['src/**/__tests__/*'],
    rules: {
      'vitest/expect-expect': 'error',
      'vitest/no-focused-tests': 'error',
      'vitest/no-disabled-tests': 'error',
    },
  },

  // No check is silenced wholesale: a disable names its rules and says why, unused ones fail.
  pluginComments.recommended,
  {
    name: 'project/directives',
    linterOptions: { reportUnusedDisableDirectives: 'error' },
    rules: {
      '@eslint-community/eslint-comments/require-description': 'error',
      '@eslint-community/eslint-comments/no-unlimited-disable': 'error',
    },
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
      // Unescaped HTML is how cross-site scripting gets in; text interpolation escapes.
      'vue/no-v-html': 'error',
      'no-restricted-imports': ['error', { patterns: [rawClient] }],
    },
  },
  // The generic CRUD and table layers work with the row type of every resource.
  {
    name: 'project/generic-layers',
    files: [
      'src/components/crud/{CrudFormDrawer.vue,CrudPage.vue,types.ts}',
      'src/components/table/{ColumnSettings.vue,TableToolbar.vue,types.ts}',
      'src/views/masterdata/resources/index.ts',
    ],
    rules: { '@typescript-eslint/no-explicit-any': 'off' },
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
