<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { PlugZap, RotateCcw, Save, FolderSync } from '@lucide/vue'
import {
  NAlert,
  NButton,
  NCheckbox,
  NCollapseTransition,
  NInput,
  NInputNumber,
  NSpin,
  NSwitch,
  NTag,
  NTooltip,
} from 'naive-ui'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { ldapSettingsApi } from '@/api/settings'
import SettingRow from '@/components/settings/SettingRow.vue'
import SettingsGroup from '@/components/settings/SettingsGroup.vue'
import { useAction } from '@/composables/useAction'

type AttrField = Extract<keyof Schemas['LdapSettingsIn'], `attr_${string}`>

const { t } = useI18n()
const router = useRouter()
const { busy: saving, run } = useAction()
const { busy: testing, run: runTest } = useAction()

/** The settings themselves, as sent and received; the bind password goes separately. */
type FieldKey = Exclude<keyof Schemas['LdapSettingsIn'], 'bind_password'>
const FIELD_KEYS: FieldKey[] = [
  'enabled',
  'server_uri',
  'start_tls',
  'verify_cert',
  'ca_cert_file',
  'timeout',
  'bind_dn',
  'user_search_base',
  'user_filter',
  'attr_username',
  'attr_first_name',
  'attr_last_name',
  'attr_employee_number',
  'attr_email',
  'attr_job_title',
  'attr_phone',
  'create_users',
]

// Argus field -> LDAP attribute; the three core fields first.
const MAPPING: { key: AttrField; label: string; result: string; required?: boolean }[] = [
  { key: 'attr_first_name', label: 'attrFirstName', result: 'first_name' },
  { key: 'attr_last_name', label: 'attrLastName', result: 'last_name' },
  { key: 'attr_employee_number', label: 'attrEmployeeNumber', result: 'employee_number' },
  { key: 'attr_email', label: 'attrEmail', result: 'email' },
  { key: 'attr_job_title', label: 'attrJobTitle', result: 'job_title' },
  { key: 'attr_phone', label: 'attrPhone', result: 'phone' },
  { key: 'attr_username', label: 'attrUsername', result: 'username', required: true },
]

const loaded = ref<Schemas['LdapSettingsOut'] | null>(null)
const form = reactive({} as Schemas['LdapSettingsIn'])
const bindPassword = ref('')
const clearPassword = ref(false)
const showAdvanced = ref(false)
const testUsername = ref('')
const testResult = ref<Schemas['LdapTestOut'] | null>(null)

const lockedBy = (field: keyof Schemas['LdapSettingsIn']) =>
  loaded.value?.locked.includes(field)
    ? t('settings.ldap.envLocked', { name: loaded.value.env_names[field] })
    : undefined
const passwordSet = computed(() => loaded.value?.bind_password_set ?? false)
const isLocked = (field: keyof Schemas['LdapSettingsIn']) => lockedBy(field) !== undefined

function apply(settings: Schemas['LdapSettingsOut']) {
  loaded.value = settings
  for (const key of FIELD_KEYS) Object.assign(form, { [key]: settings[key] })
  bindPassword.value = ''
  clearPassword.value = false
}

async function load() {
  apply(await ldapSettingsApi.get())
  // Open the advanced block when it holds something other than the defaults.
  showAdvanced.value = Boolean(form.ca_cert_file) || form.timeout !== 5
}
onMounted(load)

const dirty = computed(
  () =>
    loaded.value !== null &&
    (FIELD_KEYS.some((key) => form[key] !== loaded.value![key]) ||
      bindPassword.value !== '' ||
      clearPassword.value),
)

// The sync runs on the saved configuration only.
const syncBlocked = computed(() =>
  !loaded.value?.enabled
    ? t('settings.ldap.sync.needsEnabled')
    : dirty.value
      ? t('settings.ldap.sync.needsSave')
      : undefined,
)

const missingRequired = computed(
  () =>
    form.enabled &&
    (!form.server_uri || !form.user_search_base || !form.user_filter || !form.attr_username),
)

function payload(): Schemas['LdapSettingsIn'] {
  return { ...form, bind_password: clearPassword.value ? '' : bindPassword.value || null }
}

async function save() {
  const result = await run(() => ldapSettingsApi.update(payload()), t('common.saved'))
  if (result) apply(result)
}

async function test() {
  testResult.value = null
  const result = await runTest(() =>
    ldapSettingsApi.test({ ...payload(), username: testUsername.value.trim() }),
  )
  if (result) testResult.value = result
}

const testRows = computed(() => {
  const user = testResult.value?.user
  if (!user) return []
  return [
    { label: 'DN', value: user.dn },
    ...MAPPING.filter((m) => m.result in user).map((m) => ({
      label: t(`settings.ldap.${m.label}`),
      value: user[m.result],
    })),
  ]
})
</script>

<template>
  <NSpin :show="!loaded">
    <div v-if="loaded" class="ldap">
      <header class="head">
        <div>
          <h2>
            {{ t('settings.sections.ldap') }}
            <NTag :type="loaded.enabled ? 'success' : 'default'" size="small" :bordered="false">
              {{ loaded.enabled ? t('settings.ldap.active') : t('settings.ldap.inactive') }}
            </NTag>
          </h2>
          <p class="muted">{{ t('settings.ldap.subtitle') }}</p>
        </div>
        <NTooltip :disabled="!syncBlocked">
          <template #trigger>
            <!-- A disabled button gets no hover events; the span carries the tooltip. -->
            <span>
              <NButton
                :disabled="Boolean(syncBlocked)"
                @click="router.push({ name: 'settings-ldap-sync' })"
              >
                <template #icon><FolderSync :size="15" /></template>
                {{ t('settings.ldap.sync.open') }}
              </NButton>
            </span>
          </template>
          {{ syncBlocked }}
        </NTooltip>
      </header>

      <NAlert v-if="loaded.locked.length" type="info" :bordered="false" class="env-notice">
        {{ t('settings.ldap.envNotice', { count: loaded.locked.length }) }}
      </NAlert>

      <SettingsGroup
        :title="t('settings.ldap.groupStatus')"
        :description="t('settings.ldap.groupStatusHelp')"
      >
        <SettingRow :label="t('settings.ldap.enabled')" :locked-by="lockedBy('enabled')">
          <NSwitch v-model:value="form.enabled" :disabled="isLocked('enabled')" />
        </SettingRow>
        <SettingRow
          :label="t('settings.ldap.createUsers')"
          :help="t('settings.ldap.createUsersHelp')"
          :locked-by="lockedBy('create_users')"
        >
          <NSwitch v-model:value="form.create_users" :disabled="isLocked('create_users')" />
        </SettingRow>
      </SettingsGroup>

      <SettingsGroup
        :title="t('settings.ldap.server')"
        :description="t('settings.ldap.groupServerHelp')"
      >
        <SettingRow
          :label="t('settings.ldap.serverUri')"
          :help="t('settings.ldap.serverUriHelp')"
          :locked-by="lockedBy('server_uri')"
          :required="form.enabled"
        >
          <NInput
            v-model:value="form.server_uri"
            :disabled="isLocked('server_uri')"
            placeholder="ldaps://dc1.example.com"
            class="mono-input"
          />
        </SettingRow>
        <SettingRow
          :label="t('settings.ldap.startTls')"
          :help="t('settings.ldap.startTlsHelp')"
          :locked-by="lockedBy('start_tls')"
        >
          <NSwitch v-model:value="form.start_tls" :disabled="isLocked('start_tls')" />
        </SettingRow>
        <SettingRow :label="t('settings.ldap.verifyCert')" :locked-by="lockedBy('verify_cert')">
          <NSwitch v-model:value="form.verify_cert" :disabled="isLocked('verify_cert')" />
        </SettingRow>
        <NCollapseTransition :show="showAdvanced">
          <SettingRow
            :label="t('settings.ldap.caCertFile')"
            :help="t('settings.ldap.caCertFileHelp')"
            :locked-by="lockedBy('ca_cert_file')"
          >
            <NInput
              v-model:value="form.ca_cert_file"
              :disabled="isLocked('ca_cert_file')"
              placeholder="/app/certs/ca.pem"
              class="mono-input"
            />
          </SettingRow>
          <SettingRow :label="t('settings.ldap.timeout')" :locked-by="lockedBy('timeout')">
            <NInputNumber
              v-model:value="form.timeout"
              :min="1"
              :max="120"
              :disabled="isLocked('timeout')"
              class="narrow"
            />
          </SettingRow>
        </NCollapseTransition>
        <NButton text size="small" class="advanced-toggle" @click="showAdvanced = !showAdvanced">
          {{ showAdvanced ? t('settings.ldap.hideAdvanced') : t('settings.ldap.showAdvanced') }}
        </NButton>
      </SettingsGroup>

      <SettingsGroup
        :title="t('settings.ldap.search')"
        :description="t('settings.ldap.groupSearchHelp')"
      >
        <SettingRow
          :label="t('settings.ldap.bindDn')"
          :help="t('settings.ldap.bindDnHelp')"
          :locked-by="lockedBy('bind_dn')"
        >
          <NInput
            v-model:value="form.bind_dn"
            :disabled="isLocked('bind_dn')"
            placeholder="CN=svc-argus,OU=Service,DC=example,DC=com"
            class="mono-input"
          />
        </SettingRow>
        <SettingRow :label="t('settings.ldap.bindPassword')" :locked-by="lockedBy('bind_password')">
          <NInput
            v-model:value="bindPassword"
            type="password"
            show-password-on="click"
            :disabled="isLocked('bind_password') || clearPassword"
            :placeholder="passwordSet ? t('settings.ldap.bindPasswordKeep') : ''"
            :input-props="{ autocomplete: 'new-password' }"
          />
          <NCheckbox
            v-if="passwordSet && !isLocked('bind_password')"
            v-model:checked="clearPassword"
            size="small"
            class="clear-password"
          >
            {{ t('settings.ldap.clearPassword') }}
          </NCheckbox>
        </SettingRow>
        <SettingRow
          :label="t('settings.ldap.searchBase')"
          :locked-by="lockedBy('user_search_base')"
          :required="form.enabled"
        >
          <NInput
            v-model:value="form.user_search_base"
            :disabled="isLocked('user_search_base')"
            placeholder="OU=Staff,DC=example,DC=com"
            class="mono-input"
          />
        </SettingRow>
        <SettingRow
          :label="t('settings.ldap.userFilter')"
          :help="t('settings.ldap.userFilterHelp')"
          :locked-by="lockedBy('user_filter')"
          :required="form.enabled"
        >
          <NInput
            v-model:value="form.user_filter"
            :disabled="isLocked('user_filter')"
            class="mono-input"
          />
        </SettingRow>
      </SettingsGroup>

      <SettingsGroup
        :title="t('settings.ldap.mapping')"
        :description="t('settings.ldap.mappingHelp')"
      >
        <div class="mapping-head eyebrow">
          <span>{{ t('settings.ldap.argusField') }}</span>
          <span>{{ t('settings.ldap.ldapAttribute') }}</span>
        </div>
        <SettingRow
          v-for="m in MAPPING"
          :key="m.key"
          :label="t(`settings.ldap.${m.label}`)"
          :locked-by="lockedBy(m.key)"
          :required="m.required"
        >
          <NInput
            v-model:value="form[m.key]"
            :disabled="isLocked(m.key)"
            :placeholder="t('settings.ldap.notSynced')"
            class="mono-input"
          />
        </SettingRow>
      </SettingsGroup>

      <SettingsGroup :title="t('settings.ldap.test')" :description="t('settings.ldap.testHelp')">
        <div class="test-row">
          <NInput
            v-model:value="testUsername"
            :placeholder="t('settings.ldap.testUser')"
            class="mono-input"
            @keydown.enter.prevent="test"
          />
          <NButton :loading="testing" :disabled="!form.server_uri" @click="test">
            <template #icon><PlugZap :size="15" /></template>
            {{ t('settings.ldap.test') }}
          </NButton>
        </div>
        <template v-if="testResult">
          <NAlert type="success" :bordered="false" class="test-result">
            {{ t('settings.ldap.testOk', { server: testResult.server }) }}
            <template v-if="testRows.length">
              <br />{{ t('settings.ldap.testUserFound') }}
            </template>
          </NAlert>
          <dl v-if="testRows.length" class="result">
            <template v-for="row in testRows" :key="row.label">
              <dt>{{ row.label }}</dt>
              <dd class="mono">{{ row.value || '—' }}</dd>
            </template>
          </dl>
        </template>
      </SettingsGroup>

      <Transition name="save-bar">
        <div v-if="dirty" class="save-bar">
          <span>{{ t('settings.unsaved') }}</span>
          <div class="row">
            <NButton size="small" :disabled="saving" @click="apply(loaded)">
              <template #icon><RotateCcw :size="14" /></template>
              {{ t('common.reset') }}
            </NButton>
            <NButton
              size="small"
              type="primary"
              :loading="saving"
              :disabled="missingRequired"
              @click="save"
            >
              <template #icon><Save :size="14" /></template>
              {{ t('common.save') }}
            </NButton>
          </div>
        </div>
      </Transition>
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
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
.head p {
  margin: 4px 0 0;
  max-width: 70ch;
  font-size: 13px;
}
.env-notice {
  margin-bottom: 18px;
}
.mono-input :deep(input) {
  font-family: var(--ar-font-mono);
}
.narrow {
  width: 140px;
}
.advanced-toggle {
  margin: 2px 0 12px;
  font-size: 12.5px;
}
.clear-password {
  margin-top: 6px;
}
.mapping-head {
  display: grid;
  grid-template-columns: minmax(140px, 200px) minmax(0, 1fr);
  gap: 16px;
  padding: 10px 0 2px;
}
.test-row {
  display: flex;
  gap: 8px;
  padding: 12px 0;
}
.test-result {
  margin-bottom: 12px;
}
.result {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 6px 16px;
  margin: 0 0 14px;
}
.result dt {
  color: var(--ar-text-muted);
  font-size: 12.5px;
}
.result dd {
  margin: 0;
  overflow-wrap: anywhere;
}
/* Appears while there are unsaved changes and stays in view while scrolling. */
.save-bar {
  position: sticky;
  bottom: 12px;
  z-index: 2;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 16px;
  margin-top: 8px;
  padding: 10px 14px;
  background: var(--ar-surface-raised);
  border: 1px solid var(--ar-border-strong);
  border-left: 3px solid var(--ar-primary);
  border-radius: 3px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18);
  font-size: 13px;
}
.save-bar-enter-active,
.save-bar-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}
.save-bar-enter-from,
.save-bar-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
@container (max-width: 440px) {
  .mapping-head {
    display: none;
  }
}
</style>
