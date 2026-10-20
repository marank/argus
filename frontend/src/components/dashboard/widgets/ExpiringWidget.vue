<script setup lang="ts">
import { KeyRound, ShieldAlert } from '@lucide/vue'
import { NCard, NSkeleton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import { kindColor } from '@/components/calendar/kinds'
import { useLive } from '@/composables/useLive'
import { useFeaturesStore } from '@/stores/features'
import type { ExpiringItem, WidgetProps } from '@/types/dashboard'

import { useDateMode } from './dateMode'
import DateModeToggle from './DateModeToggle.vue'

/** Licenses and warranties ending within the warning periods of the site rules. */
const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const ICONS = { license: KeyRound, warranty: ShieldAlert }

const { t } = useI18n()
const features = useFeaturesStore()
const { mode, setMode, when, other } = useDateMode(
  () => props.options,
  (options) => emit('update:options', options),
)
const items = ref<ExpiringItem[] | null>(null)
const load = async () => (items.value = await dashboardApi.expiring())
onMounted(load)
useLive(['license', 'asset'], load)

const shown = computed(() =>
  (items.value ?? []).filter((i) => i.kind !== 'license' || features.isOn('licenses')),
)
const route = (item: ExpiringItem) =>
  item.kind === 'license'
    ? { name: 'license', params: { id: item.id } }
    : { name: 'asset', params: { id: item.id } }
</script>

<template>
  <NCard :title="t('dashboard.widgets.expiring.title')" size="small">
    <template #header-extra>
      <DateModeToggle :model-value="mode" @update:model-value="setMode" />
    </template>
    <NSkeleton v-if="!items" text :repeat="3" />
    <p v-else-if="!shown.length" class="muted">{{ t('dashboard.widgets.expiring.empty') }}</p>
    <div v-else class="lines cols-3">
      <RouterLink
        v-for="item in shown"
        :key="`${item.kind}-${item.id}`"
        :to="route(item)"
        class="line"
        :style="{ '--tone': kindColor(item.kind) }"
      >
        <component
          :is="ICONS[item.kind]"
          :size="14"
          class="icon"
          :aria-label="t(`calendar.kinds.${item.kind}`)"
        />
        <span class="title"
          >{{ item.label
          }}<small class="muted">
            · {{ item.detail || t(`calendar.kinds.${item.kind}`) }}</small
          ></span
        >
        <span
          class="when"
          :class="{ 'mono muted full': mode === 'full' }"
          :title="other(item.ends_on)"
          >{{ when(item.ends_on) }}</span
        >
      </RouterLink>
    </div>
  </NCard>
</template>

<style scoped src="./lines.css"></style>
<style scoped>
.icon {
  color: var(--tone);
}
</style>
