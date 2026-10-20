<script setup lang="ts">
import { Settings2 } from '@lucide/vue'
import { NButton, NCard, NCheckbox, NCheckboxGroup, NPopover } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { NAVIGATION, type NavItem } from '@/components/layout/navigation'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'
import type { WidgetProps } from '@/types/dashboard'

/** Links to the pages the user picked, as large buttons. */
const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const DEFAULT_KEYS = ['portal-new', 'reservations', 'calendar', 'assets', 'orders']

const { t } = useI18n()
const auth = useAuthStore()
const features = useFeaturesStore()

/** Every page of the navigation the user can open, except the dashboard itself. */
const candidates = computed<NavItem[]>(() =>
  NAVIGATION.filter((section) => !section.superuser || auth.isSuperuser)
    .flatMap((section) => section.items)
    .filter((item) => item.key !== 'dashboard' && (!item.module || features.isOn(item.module))),
)

const keys = computed<string[]>(() =>
  Array.isArray(props.options.keys) ? (props.options.keys as string[]) : DEFAULT_KEYS,
)
/** In the order of the navigation, so the buttons stay where one expects them. */
const shortcuts = computed(() => candidates.value.filter((item) => keys.value.includes(item.key)))

const choose = (value: (string | number)[]) =>
  emit('update:options', { ...props.options, keys: value.map(String) })
</script>

<template>
  <NCard :title="title ?? t('dashboard.widgets.shortcuts.title')" size="small">
    <template #header-extra>
      <NPopover trigger="click" placement="bottom-end" scrollable style="max-height: 360px">
        <template #trigger>
          <NButton quaternary size="tiny" :title="t('dashboard.widgets.shortcuts.choose')">
            <template #icon><Settings2 /></template>
          </NButton>
        </template>
        <NCheckboxGroup :value="keys" @update:value="choose">
          <div class="choices">
            <NCheckbox
              v-for="item in candidates"
              :key="item.key"
              :value="item.key"
              :label="t(item.label)"
            />
          </div>
        </NCheckboxGroup>
      </NPopover>
    </template>
    <p v-if="!shortcuts.length" class="muted">{{ t('dashboard.widgets.shortcuts.empty') }}</p>
    <div v-else class="shortcuts">
      <RouterLink v-for="item in shortcuts" :key="item.key" :to="item.to" class="shortcut">
        <component :is="item.icon" :size="16" />
        <span>{{ t(item.label) }}</span>
      </RouterLink>
    </div>
  </NCard>
</template>

<style scoped>
.shortcuts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 8px;
}
/* A third of the page (at most ~470px) fits three cramped buttons; two read better. */
@container (max-width: 480px) {
  .shortcuts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
.shortcut {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  color: inherit;
  text-decoration: none;
  transition: background-color 0.15s ease;
}
.shortcut svg {
  flex: none;
  color: var(--ar-primary);
}
.shortcut span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.shortcut:hover,
.shortcut:focus-visible {
  border-color: var(--ar-primary);
  background: var(--ar-surface-sunken);
  text-decoration: none;
}
.choices {
  display: grid;
  gap: 6px;
  padding: 4px 2px;
}
</style>
