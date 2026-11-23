import { globalIgnores } from 'eslint/config'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import pluginVitest from '@vitest/eslint-plugin'
import pluginOxlint from 'eslint-plugin-oxlint'
import sonarjs from 'eslint-plugin-sonarjs'
import pluginA11y from 'eslint-plugin-vuejs-accessibility'
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

  ...pluginVue.configs['flat/strongly-recommended'],
  vueTsConfigs.recommendedTypeChecked,
  // Missing alt texts, unlabelled fields, clickable elements without keyboard access.
  ...pluginA11y.configs['flat/recommended'],

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
    plugins: { sonarjs },
    rules: {
      // "modified": a switch counts once, so a flat dispatch over many cases is fine.
      complexity: ['error', { max: 15, variant: 'modified' }],
      // How hard a function is to follow: nesting costs more than a flat list of cases.
      'sonarjs/cognitive-complexity': ['error', 15],
      // Checks the types already rule out, promises nobody awaits, switches missing a case,
      // defaults that would replace 0 or an empty string.
      '@typescript-eslint/no-unnecessary-condition': 'error',
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/no-misused-promises': 'error',
      '@typescript-eslint/switch-exhaustiveness-check': 'error',
      // An empty text gets the placeholder as well, so || stays right for strings.
      '@typescript-eslint/prefer-nullish-coalescing': ['error', { ignorePrimitives: { string: true } }],
      // Reports assertions that keep a literal from widening (in reactive() and defaults);
      // removing them breaks vue-tsc, so the rule only gets in the way.
      '@typescript-eslint/no-unnecessary-type-assertion': 'off',
      'max-depth': ['error', 4],
      // Unescaped HTML is how cross-site scripting gets in; text interpolation escapes.
      'vue/no-v-html': 'error',
      // A label names its field by nesting it or by `for`; Naive UI's inputs are components.
      'vuejs-accessibility/label-has-for': [
        'error',
        {
          required: { some: ['nesting', 'id'] },
          controlComponents: ['NSwitch', 'NCheckbox', 'NInput', 'NSelect'],
        },
      ],
      // Dialogs focus their first field when they open; only native elements are checked.
      'vuejs-accessibility/no-autofocus': ['error', { ignoreNonDOM: true }],
      // Props, data and computed nobody uses are dead weight or a forgotten wiring.
      'vue/no-unused-properties': [
        'error',
        { groups: ['props', 'data', 'computed', 'methods', 'setup'] },
      ],
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
  // Every widget gets the same WidgetProps from the dashboard, used or not.
  {
    name: 'project/widgets',
    files: ['src/components/dashboard/widgets/*.vue'],
    rules: { 'vue/no-unused-properties': 'off' },
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
  // Tests check at runtime what the types promise, pass mocked methods around unbound and
  // write async mocks that return at once; the app code keeps these rules.
  {
    name: 'project/tests-typed',
    files: ['src/**/__tests__/*'],
    rules: {
      '@typescript-eslint/no-unnecessary-condition': 'off',
      '@typescript-eslint/require-await': 'off',
      '@typescript-eslint/unbound-method': 'off',
    },
  },
)
