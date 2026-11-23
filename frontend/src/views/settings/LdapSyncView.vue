<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { ArrowLeft, ArrowRight, Play } from '@lucide/vue'
import {
  NAlert,
  NButton,
  NDataTable,
  NInput,
  NSpin,
  NTooltip,
  useMessage,
  type DataTableColumns,
} from 'naive-ui'
import { useStorage } from '@vueuse/core'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { ldapSettingsApi } from '@/api/settings'
import StatusTag from '@/components/common/StatusTag.vue'
import SettingsGroup from '@/components/settings/SettingsGroup.vue'
import { useAction } from '@/composables/useAction'

const { t } = useI18n()
const message = useMessage()
const { busy: searching, run: runSearch } = useAction()
const { busy: applying, run: runApply } = useAction()

const ACTIONS: Schemas['LdapSyncItemOut']['action'][] = ['create', 'update', 'unchanged', 'skipped']
const SELECTABLE: Schemas['LdapSyncItemOut']['action'][] = ['create', 'update']

// Argus field -> label key, in the order the changes are listed.
const FIELD_LABELS: Record<string, string> = {
  username: 'attrUsername',
  first_name: 'attrFirstName',
  last_name: 'attrLastName',
  employee_number: 'attrEmployeeNumber',
  email: 'attrEmail',
  job_title: 'attrJobTitle',
  phone: 'attrPhone',
}

// The sync runs on the saved configuration, so that is what the page shows.
const settings = ref<Schemas['LdapSettingsOut'] | null>(null)
const usable = computed(
  () =>
    settings.value !== null &&
    settings.value.enabled &&
    Boolean(settings.value.server_uri && settings.value.user_search_base),
)

/** The login filter with {username} as wildcard: everyone who could sign in. */
const loginFilter = computed(() =>
  (settings.value?.user_filter ?? '').replaceAll('{username}', '*'),
)
const presets = computed(() => [
  { label: t('settings.ldap.sync.presetLogin'), filter: loginFilter.value },
  {
    label: t('settings.ldap.sync.presetActive'),
    filter: `(&${loginFilter.value}(!(userAccountControl:1.2.840.113556.1.4.803:=2)))`,
  },
  {
    label: t('settings.ldap.sync.presetGroup'),
    filter: `(&${loginFilter.value}(memberOf=CN=Gruppe,OU=Groups,DC=example,DC=com))`,
  },
])

// The last query is kept per browser, so a recurring sync is one click.
const filter = useStorage('argus.ldap-sync-filter', '')
const searchBase = useStorage('argus.ldap-sync-base', '')
onMounted(async () => {
  settings.value = await ldapSettingsApi.get()
  if (!filter.value) filter.value = loginFilter.value
})

const preview = ref<Schemas['LdapSyncPreviewOut'] | null>(null)
/** The query the preview ran with; applying uses it, not the (possibly edited) editor. */
const previewQuery = ref<Schemas['LdapSyncQueryIn'] | null>(null)
const checked = ref<string[]>([])
const visible = ref<Schemas['LdapSyncItemOut']['action'][]>(['create', 'update', 'skipped'])
const search = ref('')

const stale = computed(
  () =>
    previewQuery.value !== null &&
    (previewQuery.value.filter !== filter.value.trim() ||
      previewQuery.value.search_base !== searchBase.value.trim()),
)

/** Ctrl+Enter (Cmd+Enter on a Mac) in the filter runs the preview. */
function previewOnShortcut(event: KeyboardEvent) {
  if (event.key !== 'Enter' || !(event.ctrlKey || event.metaKey)) return
  event.preventDefault()
  void runPreview()
}

async function runPreview() {
  const query = { filter: filter.value.trim(), search_base: searchBase.value.trim() }
  const result = await runSearch(() => ldapSettingsApi.syncPreview(query))
  if (!result) return
  preview.value = result
  previewQuery.value = query
  checked.value = result.items.filter((i) => SELECTABLE.includes(i.action)).map((i) => i.dn)
}

async function apply() {
  const query = previewQuery.value!
  const result = await runApply(() => ldapSettingsApi.syncApply({ ...query, dns: checked.value }))
  if (!result) return
  message.success(t('settings.ldap.sync.applied', { ...result }))
  // Show what is left; the taken-over entries now read "unchanged".
  filter.value = query.filter
  searchBase.value = query.search_base
  await runPreview()
}

const counts = computed(() => {
  const result = Object.fromEntries(ACTIONS.map((a) => [a, 0])) as Record<
    Schemas['LdapSyncItemOut']['action'],
    number
  >
  for (const item of preview.value?.items ?? []) result[item.action]++
  return result
})

function toggle(action: Schemas['LdapSyncItemOut']['action']) {
  visible.value = visible.value.includes(action)
    ? visible.value.filter((a) => a !== action)
    : [...visible.value, action]
}

const rows = computed(() => {
  const needle = search.value.trim().toLowerCase()
  return (preview.value?.items ?? []).filter(
    (i) =>
      visible.value.includes(i.action) &&
      (!needle ||
        [i.username, i.dn, ...Object.values(i.values)].some((v) =>
          v.toLowerCase().includes(needle),
        )),
  )
})

const fieldLabel = (field: string) =>
  FIELD_LABELS[field] ? t(`settings.ldap.${FIELD_LABELS[field]}`) : field

function renderChanges(item: Schemas['LdapSyncItemOut']) {
  if (item.action === 'skipped') {
    return h('span', { class: 'muted' }, t(`settings.ldap.sync.reason.${item.reason}`))
  }
  if (item.action !== 'update') return null
  return h(
    'ul',
    { class: 'changes' },
    Object.entries(item.changes).map(([field, change]) =>
      field === 'ldap_dn'
        ? h('li', { class: 'muted' }, t('settings.ldap.sync.linked'))
        : h('li', [
            h('span', { class: 'field' }, fieldLabel(field)),
            h('span', { class: 'old' }, change.old || '—'),
            h(ArrowRight, { size: 12, class: 'arrow' }),
            h('span', { class: 'new' }, change.new || '—'),
          ]),
    ),
  )
}

const columns = computed<DataTableColumns<Schemas['LdapSyncItemOut']>>(() => [
  {
    type: 'selection',
    disabled: (i) => !SELECTABLE.includes(i.action),
  },
  {
    key: 'action',
    title: t('settings.ldap.sync.action'),
    width: 120,
    render: (i) => h(StatusTag, { group: 'ldapSync', value: i.action }),
  },
  {
    key: 'username',
    title: t('settings.ldap.attrUsername'),
    width: 125,
    render: (i) =>
      h(
        NTooltip,
        { placement: 'top-start' },
        {
          trigger: () => h('span', { class: 'mono strong' }, i.username || '—'),
          default: () => i.dn,
        },
      ),
  },
  {
    key: 'name',
    title: t('settings.ldap.sync.name'),
    width: 145,
    render: (i) => [i.values.first_name, i.values.last_name].filter(Boolean).join(' ') || '—',
  },
  {
    key: 'employee_number',
    title: t('settings.ldap.attrEmployeeNumber'),
    width: 100,
    render: (i) => h('span', { class: 'mono' }, i.values.employee_number || '—'),
  },
  {
    key: 'email',
    title: t('settings.ldap.attrEmail'),
    width: 180,
    ellipsis: { tooltip: true },
    render: (i) => i.values.email || '—',
  },
  {
    key: 'changes',
    title: t('settings.ldap.sync.changes'),
    minWidth: 200,
    render: renderChanges,
  },
])
</script>

<template>
  <NSpin :show="!settings">
    <div v-if="settings" class="ldap-sync">
      <header class="head">
        <div>
          <h2>{{ t('settings.ldap.sync.title') }}</h2>
          <p class="muted">{{ t('settings.ldap.sync.help') }}</p>
        </div>
        <RouterLink :to="{ name: 'settings-ldap' }">
          <NButton quaternary>
            <template #icon><ArrowLeft :size="15" /></template>
            {{ t('settings.ldap.sync.back') }}
          </NButton>
        </RouterLink>
      </header>

      <NAlert v-if="!usable" type="warning" :bordered="false" class="notice">
        {{ t('settings.ldap.sync.needsEnabled') }}
      </NAlert>

      <SettingsGroup
        :title="t('settings.ldap.sync.query')"
        :description="t('settings.ldap.sync.queryHelp')"
      >
        <div class="editor">
          <label class="eyebrow" for="ldap-sync-base">{{ t('settings.ldap.searchBase') }}</label>
          <NInput
            v-model:value="searchBase"
            :input-props="{ id: 'ldap-sync-base' }"
            :placeholder="settings.user_search_base"
            class="mono-input"
          />
          <label class="eyebrow" for="ldap-sync-filter">{{ t('settings.ldap.sync.filter') }}</label>
          <div>
            <NInput
              v-model:value="filter"
              type="textarea"
              class="mono-input"
              :input-props="{ id: 'ldap-sync-filter', spellcheck: false }"
              :autosize="{ minRows: 3, maxRows: 10 }"
              @keydown="previewOnShortcut"
            />
            <div class="editor-foot">
              <div class="presets">
                <span class="muted">{{ t('settings.ldap.sync.presets') }}</span>
                <NButton
                  v-for="p in presets"
                  :key="p.label"
                  size="tiny"
                  secondary
                  @click="filter = p.filter"
                >
                  {{ p.label }}
                </NButton>
              </div>
              <NButton
                type="primary"
                :loading="searching"
                :disabled="!usable || !filter.trim()"
                @click="runPreview"
              >
                <template #icon><Play :size="14" /></template>
                {{ t('settings.ldap.sync.run') }}
                <kbd>Ctrl ↵</kbd>
              </NButton>
            </div>
          </div>
        </div>
      </SettingsGroup>

      <section v-if="preview" class="results">
        <NAlert v-if="preview.truncated" type="warning" :bordered="false" class="notice">
          {{ t('settings.ldap.sync.truncated', { limit: preview.limit }) }}
        </NAlert>
        <NAlert v-if="stale" type="info" :bordered="false" class="notice">
          {{ t('settings.ldap.sync.stale') }}
        </NAlert>

        <div class="toolbar">
          <div class="chips">
            <button
              v-for="a in ACTIONS"
              :key="a"
              type="button"
              class="chip"
              :class="{ on: visible.includes(a) }"
              :aria-pressed="visible.includes(a)"
              @click="toggle(a)"
            >
              <StatusTag group="ldapSync" :value="a" />
              <span class="count">{{ counts[a] }}</span>
            </button>
          </div>
          <NInput
            v-model:value="search"
            size="small"
            clearable
            :placeholder="t('settings.ldap.sync.search')"
            class="search"
          />
        </div>

        <NDataTable
          v-model:checked-row-keys="checked"
          size="small"
          :columns="columns"
          :data="rows"
          :row-key="(i: Schemas['LdapSyncItemOut']) => i.dn"
          :pagination="{ pageSize: 50 }"
          :scroll-x="900"
        />

        <!-- Stays in view while scrolling through a long preview, like the settings save bar. -->
        <div class="apply-bar">
          <span>{{ t('settings.ldap.sync.selected', { count: checked.length }) }}</span>
          <NButton
            type="primary"
            size="small"
            :loading="applying"
            :disabled="!checked.length || searching"
            @click="apply"
          >
            {{ t('settings.ldap.sync.apply', { count: checked.length }) }}
          </NButton>
        </div>
      </section>
    </div>
  </NSpin>
</template>

<style scoped>
.head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px 24px;
  margin-bottom: 18px;
}
h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
.head p {
  margin: 4px 0 0;
  max-width: 70ch;
  font-size: 13px;
}
.editor {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  align-items: start;
  gap: 10px 16px;
  padding: 14px 0;
}
.editor label {
  padding-top: 7px;
}
.mono-input :deep(input),
.mono-input :deep(textarea) {
  font-family: var(--ar-font-mono);
  font-size: 12.5px;
}
.editor-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 16px;
  margin-top: 8px;
}
.presets {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}
kbd {
  margin-left: 8px;
  padding: 0 4px;
  border: 1px solid color-mix(in srgb, currentColor 35%, transparent);
  border-radius: 2px;
  font-family: var(--ar-font-mono);
  font-size: 10.5px;
  opacity: 0.8;
}
.notice {
  margin-bottom: 12px;
}
.results {
  padding-top: 22px;
  border-top: 1px solid var(--ar-border);
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 16px;
  margin-bottom: 10px;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 3px 8px 3px 4px;
  border: 1px solid var(--ar-border-strong);
  border-radius: 3px;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
  opacity: 0.5;
}
.chip.on {
  opacity: 1;
}
.count {
  font-family: var(--ar-font-mono);
  font-size: 12px;
  font-weight: 600;
}
.search {
  width: 240px;
}
:deep(.changes) {
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 12.5px;
}
:deep(.changes li) {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px 6px;
}
:deep(.changes .field) {
  color: var(--ar-text-muted);
}
:deep(.changes .old) {
  text-decoration: line-through;
  opacity: 0.65;
}
:deep(.changes .arrow) {
  color: var(--ar-text-muted);
}
.apply-bar {
  position: sticky;
  bottom: 12px;
  z-index: 2;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 16px;
  margin-top: 12px;
  padding: 10px 14px;
  background: var(--ar-surface-raised);
  border: 1px solid var(--ar-border-strong);
  border-left: 3px solid var(--ar-primary);
  border-radius: 3px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18);
  font-size: 13px;
}
@media (max-width: 640px) {
  .editor {
    grid-template-columns: minmax(0, 1fr);
  }
  .editor label {
    padding-top: 0;
  }
  .search {
    width: 100%;
  }
}
</style>
