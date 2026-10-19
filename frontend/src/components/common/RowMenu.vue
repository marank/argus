<script setup lang="ts">
import { EllipsisVertical } from '@lucide/vue'
import { NButton, NDropdown, type DropdownOption } from 'naive-ui'
import { computed, h, ref, type Component } from 'vue'

export interface RowMenuItem {
  key: string
  label: string
  icon?: Component
  danger?: boolean
  /** Draw a divider above this item. */
  divided?: boolean
}

/** Vertical "⋮" menu for row actions; stays visible while open (see `.row-actions`). */
const props = defineProps<{ items: RowMenuItem[]; title?: string }>()
const emit = defineEmits<{ select: [key: string] }>()
const open = ref(false)

const options = computed<DropdownOption[]>(() =>
  props.items.flatMap((item) => [
    ...(item.divided ? [{ type: 'divider', key: `${item.key}-divider` }] : []),
    {
      key: item.key,
      label: item.label,
      icon: item.icon ? () => h(item.icon!, { size: 15 }) : undefined,
      props: item.danger ? { style: 'color: var(--ar-error)' } : undefined,
    },
  ]),
)
</script>

<template>
  <NDropdown
    trigger="click"
    placement="bottom-end"
    :options="options"
    @update:show="(value: boolean) => (open = value)"
    @select="(key: string) => emit('select', key)"
  >
    <NButton
      quaternary
      size="tiny"
      class="row-actions"
      :class="{ 'is-open': open }"
      :title="title"
      @click.stop
    >
      <template #icon><EllipsisVertical :size="16" /></template>
    </NButton>
  </NDropdown>
</template>
