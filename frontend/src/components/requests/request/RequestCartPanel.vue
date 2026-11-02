<script setup lang="ts">
import { Pencil, Send, ShoppingCart, X } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import RequestCart from './RequestCart.vue'
import type { CartLine } from './types'

/**
 * The cart as a panel like a form drawer: title on top, what was chosen in between, and
 * at the bottom the one button that sends the request. The page docks it next to the
 * catalog where there is room, and opens it as a drawer (a sheet on a phone) where not.
 */
defineProps<{
  direct?: boolean
  /** Period and purpose in one line, with the way back to change them. */
  details?: { period: string; purpose: string }
  busy?: boolean
  /** In a drawer: an X to close it. */
  closable?: boolean
}>()
const lines = defineModel<CartLine[]>('lines', { required: true })
const notes = defineModel<string>('notes', { required: true })
const emit = defineEmits<{ submit: []; edit: []; close: [] }>()
const { t } = useI18n()

const total = computed(() => lines.value.reduce((sum, line) => sum + line.quantity, 0))
</script>

<template>
  <section class="cart-panel">
    <header class="panel-head">
      <ShoppingCart :size="16" />
      <h2>{{ t('requests.new.steps.cart') }}</h2>
      <span v-if="total" :key="total" class="mono badge">{{ total }}</span>
      <NButton
        v-if="closable"
        quaternary
        circle
        size="small"
        class="panel-close"
        :aria-label="t('common.close')"
        @click="emit('close')"
      >
        <template #icon><X :size="18" /></template>
      </NButton>
    </header>

    <Transition name="ar-fade">
      <button v-if="details" type="button" class="summary" @click="emit('edit')">
        <span class="summary-text">
          <span class="mono">{{ details.period }}</span>
          <span class="purpose">{{ details.purpose }}</span>
        </span>
        <Pencil :size="14" class="summary-edit" :aria-label="t('common.edit')" />
      </button>
    </Transition>

    <div class="panel-body">
      <!-- Without the details (still on the first step) there is nothing to pick yet. -->
      <RequestCart
        v-model:lines="lines"
        v-model:notes="notes"
        :direct="direct"
        :empty-text="details ? undefined : t('requests.new.cartEmptyFirst')"
      />
    </div>

    <footer class="panel-foot">
      <NButton
        type="primary"
        block
        icon-placement="right"
        class="submit-button"
        :disabled="!lines.length"
        :loading="busy"
        @click="emit('submit')"
      >
        {{ t('requests.new.submit') }}
        <template #icon><Send :size="16" /></template>
      </NButton>
    </footer>
  </section>
</template>

<style scoped>
.cart-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 52px;
  padding: 10px 14px 10px 18px;
  border-bottom: 1px solid var(--ar-border);
  color: var(--ar-text-muted);
}
h2 {
  margin: 0;
  color: var(--ar-text);
  font-size: 14px;
  font-weight: 600;
}
.badge {
  /* Centred digits; re-keyed on change so the count pops. */
  display: inline-grid;
  place-items: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: var(--ar-primary);
  color: var(--ar-on-primary);
  font-size: 11px;
  font-weight: 700;
  animation: ar-pop 0.25s ease-out;
}
.panel-close {
  margin-left: auto;
}
/* Period and purpose of the first step: one tap leads back to change them. */
.summary {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  padding: 10px 18px;
  border: 0;
  border-bottom: 1px solid var(--ar-border);
  background: var(--ar-surface-sunken);
  color: var(--ar-text);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.summary-text {
  display: grid;
  flex: 1;
  min-width: 0;
  font-size: 12.5px;
}
.summary .mono {
  color: var(--ar-text-muted);
  font-size: 11.5px;
}
.purpose {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.summary-edit {
  flex: none;
  color: var(--ar-text-subtle);
  transition: color 0.15s ease;
}
.summary:hover .summary-edit,
.summary:focus-visible .summary-edit {
  color: var(--ar-primary);
}
.panel-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 14px 18px;
}
.panel-foot {
  padding: 12px 18px calc(12px + env(safe-area-inset-bottom));
  border-top: 1px solid var(--ar-border);
}
.submit-button {
  height: 42px;
}
</style>
