<script setup lang="ts">
import { NSkeleton, NSwitch, useMessage } from 'naive-ui'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import SettingRow from '@/components/settings/SettingRow.vue'
import SettingsGroup from '@/components/settings/SettingsGroup.vue'
import { useFeaturesStore } from '@/stores/features'
import type { FlagKey, SiteSettings } from '@/types/settings'

/**
 * One block per module: its own switch, then the features that belong to it.
 * A feature sits under the first module it needs; it is greyed out while any
 * module it needs is off. Features without a module come last under "General".
 */
const { t } = useI18n()
const message = useMessage()
const features = useFeaturesStore()

onMounted(() => features.load())

type Definition = SiteSettings['definitions'][number]

const settings = computed(() => features.settings)
const groups = computed(() => {
  const definitions = settings.value?.definitions ?? []
  const modules = definitions.filter((d) => d.kind === 'module')
  const featureDefs = definitions.filter((d) => d.kind === 'feature')
  return {
    modules: modules.map((module) => ({
      module,
      features: featureDefs.filter((f) => f.requires[0] === module.key),
    })),
    general: featureDefs.filter((f) => !f.requires.length),
  }
})

const isStored = (key: FlagKey) => settings.value?.stored[key] ?? true

/** Other modules a feature needs (besides the one it is listed under) that are off. */
function otherMissing(feature: Definition, parent?: FlagKey): string[] {
  return feature.requires
    .filter((key) => key !== parent && !isStored(key))
    .map((key) => t(`settings.flags.${key}`))
}

const featureDisabled = (feature: Definition) => feature.requires.some((key) => !isStored(key))

async function toggle(key: FlagKey, value: boolean) {
  try {
    await features.update({ [key]: value })
    message.success(
      t(value ? 'settings.flags.switchedOn' : 'settings.flags.switchedOff', {
        name: t(`settings.flags.${key}`),
      }),
    )
  } catch {
    message.error(t('common.error'))
  }
}
</script>

<template>
  <NSkeleton v-if="!settings" height="320px" />
  <div v-else>
    <SettingsGroup
      v-for="{ module, features: moduleFeatures } in groups.modules"
      :key="module.key"
      :title="t(`settings.flags.${module.key}`)"
      :description="t(`settings.flags.${module.key}Help`)"
    >
      <SettingRow :label="t('settings.flags.moduleOn')" toggle>
        <NSwitch
          :value="isStored(module.key)"
          @update:value="(value: boolean) => toggle(module.key, value)"
        />
      </SettingRow>
      <SettingRow
        v-for="feature in moduleFeatures"
        :key="feature.key"
        class="feature-row"
        :class="{ inactive: featureDisabled(feature) }"
        :label="t(`settings.flags.${feature.key}`)"
        :help="t(`settings.flags.${feature.key}Help`)"
        toggle
      >
        <div class="feature-control">
          <small v-if="otherMissing(feature, module.key).length" class="muted">
            {{
              t('settings.flags.needs', { modules: otherMissing(feature, module.key).join(', ') })
            }}
          </small>
          <NSwitch
            :value="isStored(feature.key)"
            :disabled="featureDisabled(feature)"
            @update:value="(value: boolean) => toggle(feature.key, value)"
          />
        </div>
      </SettingRow>
    </SettingsGroup>

    <SettingsGroup
      v-if="groups.general.length"
      :title="t('settings.flags.general')"
      :description="t('settings.flags.generalDescription')"
    >
      <SettingRow
        v-for="feature in groups.general"
        :key="feature.key"
        :label="t(`settings.flags.${feature.key}`)"
        :help="t(`settings.flags.${feature.key}Help`)"
        toggle
      >
        <NSwitch
          :value="isStored(feature.key)"
          @update:value="(value: boolean) => toggle(feature.key, value)"
        />
      </SettingRow>
    </SettingsGroup>
  </div>
</template>

<style scoped>
/* Features belong to the module switch above them. */
.feature-row {
  padding-left: 18px;
}
.feature-row.inactive :deep(.label) {
  color: var(--ar-text-subtle);
}
.feature-control {
  display: flex;
  align-items: center;
  gap: 10px;
}
small {
  font-size: 11.5px;
  white-space: nowrap;
}
</style>
