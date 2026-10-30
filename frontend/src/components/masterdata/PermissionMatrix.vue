<script setup lang="ts">
import { NRadioButton, NRadioGroup, NSkeleton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { rolesApi } from '@/api/accounts'
import type { Schemas } from '@/api/types'

/**
 * The rights of a role in the edit drawer: per area none, read or write.
 * Edits `form.permissions` in place; areas set to none are left out.
 */
const props = defineProps<{ form: Record<string, unknown>; readonly?: boolean }>()
const { t } = useI18n()

const resources = ref<Schemas['ResourceOut'][] | null>(null)
onMounted(async () => (resources.value = await rolesApi.resources()))

const GROUPS = ['masterdata', 'operations'] as const
const groups = computed(() =>
  GROUPS.map((group) => ({
    group,
    resources: (resources.value ?? []).filter((r) => r.group === group),
  })),
)

type Permissions = Partial<Record<string, Schemas['PermissionLevel']>>
const permissions = () => (props.form.permissions ?? {}) as Permissions

const levelOf = (key: string) => permissions()[key] ?? 'none'

function setLevel(key: string, level: Schemas['PermissionLevel'] | 'none') {
  const next = { ...permissions() }
  if (level === 'none') delete next[key]
  else next[key] = level
  // eslint-disable-next-line vue/no-mutating-props -- the drawer's form is meant to be edited
  props.form.permissions = next
}

/** Sets every area of a group at once. */
function setGroup(group: (typeof GROUPS)[number], level: Schemas['PermissionLevel'] | 'none') {
  for (const resource of groups.value.find((g) => g.group === group)?.resources ?? [])
    setLevel(resource.key, level)
}

const LEVELS = ['none', 'read', 'write'] as const
</script>

<template>
  <div class="matrix">
    <div class="eyebrow">{{ t('masterdata.roles.permissions') }}</div>
    <p class="muted small">{{ t('masterdata.roles.permissionsHelp') }}</p>
    <NSkeleton v-if="!resources" height="200px" />
    <template v-else>
      <section v-for="block in groups" :key="block.group" class="block">
        <div class="head">
          <strong>{{ t(`masterdata.roles.groups.${block.group}`) }}</strong>
          <span v-if="!readonly" class="all">
            <button
              v-for="level in LEVELS"
              :key="level"
              type="button"
              class="link"
              @click="setGroup(block.group, level)"
            >
              {{ t(`masterdata.roles.all.${level}`) }}
            </button>
          </span>
        </div>
        <div v-for="resource in block.resources" :key="resource.key" class="line">
          <span>{{ t(`masterdata.roles.areas.${resource.key}`) }}</span>
          <NRadioGroup
            :value="levelOf(resource.key)"
            size="small"
            :disabled="readonly"
            @update:value="
              (level: Schemas['PermissionLevel'] | 'none') => setLevel(resource.key, level)
            "
          >
            <NRadioButton v-for="level in LEVELS" :key="level" :value="level">
              {{ t(`masterdata.roles.levels.${level}`) }}
            </NRadioButton>
          </NRadioGroup>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.matrix {
  display: grid;
  gap: 8px;
}
.small {
  margin: 0;
  font-size: 12px;
}
.block {
  border: 1px solid var(--ar-border);
  border-radius: 3px;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--ar-border);
  background: var(--ar-surface-sunken);
  font-size: 12.5px;
}
.all {
  display: flex;
  gap: 10px;
}
.link {
  padding: 0;
  border: none;
  background: none;
  color: var(--ar-primary);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}
.line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 12px;
  font-size: 13px;
}
.line + .line {
  border-top: 1px solid var(--ar-border);
}
</style>
