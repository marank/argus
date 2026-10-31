<script setup lang="ts">
import { MessageSquarePlus, Minus, PackageSearch, Plus, Trash2 } from '@lucide/vue'
import { NButton, NInput, NInputNumber } from 'naive-ui'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { CartLine } from './types'

/**
 * What the request holds: the chosen lines and a message to IT. Period and purpose are
 * set in the first step; the page sends the request.
 * For a direct hand-out (`direct`) the lines are specific devices and stocks.
 */
defineProps<{ direct?: boolean }>()
const lines = defineModel<CartLine[]>('lines', { required: true })
const notes = defineModel<string>('notes', { required: true })
const { t } = useI18n()

const openNote = ref<string | null>(null)
const total = computed(() => lines.value.reduce((sum, line) => sum + line.quantity, 0))
</script>

<template>
  <aside class="cart">
    <header>
      <h2>{{ t('requests.new.cart') }}</h2>
      <span v-if="total" :key="total" class="mono badge">{{ total }}</span>
    </header>

    <div v-if="!lines.length" class="empty">
      <PackageSearch :size="30" :stroke-width="1.3" />
      <p>{{ direct ? t('requests.direct.cartEmpty') : t('requests.new.cartEmpty') }}</p>
    </div>

    <template v-else>
      <TransitionGroup tag="ul" name="cart-line" class="lines">
        <li v-for="(line, index) in lines" :key="line.key">
          <div class="line">
            <div class="text">
              <span v-if="line.code" class="mono code">{{ line.code }}</span>
              <strong>{{ line.label }}</strong>
              <small v-if="line.description" class="custom-hint">
                <MessageSquarePlus :size="12" /> {{ t('requests.new.customHint') }}
              </small>
              <button
                v-if="!direct"
                type="button"
                class="note-link"
                @click="openNote = openNote === line.key ? null : line.key"
              >
                {{ line.note || t('requests.new.addNote') }}
              </button>
            </div>
            <NInputNumber
              v-if="!line.asset"
              v-model:value="line.quantity"
              :min="1"
              :max="line.max ?? 500"
              size="small"
              button-placement="both"
              class="qty"
            >
              <template #minus-icon><Minus :size="12" /></template>
              <template #add-icon><Plus :size="12" /></template>
            </NInputNumber>
            <NButton
              quaternary
              circle
              size="tiny"
              :title="t('common.remove')"
              @click="lines.splice(index, 1)"
            >
              <template #icon><Trash2 :size="14" /></template>
            </NButton>
          </div>
          <NInput
            v-if="openNote === line.key"
            v-model:value="line.note"
            size="small"
            :placeholder="t('requests.new.itemNote')"
          />
          <small v-if="line.available !== null && line.quantity > line.available" class="warn">
            {{ t('requests.new.available', { count: line.available }) }}
          </small>
        </li>
      </TransitionGroup>

      <div class="details">
        <label class="eyebrow" for="request-notes">{{ t('requests.notes') }}</label>
        <NInput
          v-model:value="notes"
          type="textarea"
          :input-props="{ id: 'request-notes' }"
          :placeholder="t('requests.new.notesPlaceholder')"
          :autosize="{ minRows: 2, maxRows: 5 }"
        />
      </div>
    </template>
  </aside>
</template>

<style scoped>
/* New lines slide in, removed ones fade out. */
.cart-line-enter-active,
.cart-line-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.cart-line-enter-from,
.cart-line-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
.cart-line-move {
  transition: transform 0.2s ease;
}
.cart {
  display: grid;
  gap: 14px;
  padding: 16px 18px 18px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
.badge {
  /* Centered digits; re-keyed on change so the count pops. */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  line-height: 1;
  animation: ar-pop 0.25s ease-out;
  background: var(--ar-primary);
  color: var(--ar-on-primary);
  font-size: 11px;
  font-weight: 700;
  text-align: center;
}
.empty {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 24px 8px;
  color: var(--ar-text-subtle);
  text-align: center;
}
.empty p {
  margin: 0;
  color: var(--ar-text-muted);
}
.lines {
  display: grid;
  margin: 0;
  padding: 0;
  list-style: none;
}
.lines li {
  display: grid;
  gap: 6px;
  padding: 10px 0;
  border-bottom: 1px solid var(--ar-border);
}
.lines li:first-child {
  padding-top: 0;
}
.line {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.text {
  display: grid;
  flex: 1;
  min-width: 0;
}
.text strong {
  overflow-wrap: anywhere;
}
.custom-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--ar-text-muted);
  font-size: 11.5px;
}
.note-link {
  padding: 0;
  border: 0;
  background: none;
  color: var(--ar-text-subtle);
  font: inherit;
  font-size: 11.5px;
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.note-link:hover {
  color: var(--ar-primary);
}
.qty {
  width: 104px;
}
.qty :deep(input) {
  text-align: center;
}
.warn {
  color: var(--ar-warning);
}
.details {
  display: grid;
  gap: 6px;
  padding-top: 4px;
}
.code {
  color: var(--ar-primary);
  font-size: 11.5px;
}
</style>
