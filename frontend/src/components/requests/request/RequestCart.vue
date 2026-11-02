<script setup lang="ts">
import { MessageSquare, MessageSquarePlus, Minus, PackageSearch, Plus, Trash2 } from '@lucide/vue'
import { NButton, NInput, NInputNumber } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { CartLine } from './types'

/**
 * What the request holds: the chosen lines and a message to IT, inside the cart panel
 * (which has the title, the details and the send button).
 * For a direct hand-out (`direct`) the lines are specific devices and stocks.
 */
defineProps<{
  direct?: boolean
  /** What an empty cart says instead of the default, e.g. before the selection step. */
  emptyText?: string
}>()
const lines = defineModel<CartLine[]>('lines', { required: true })
const notes = defineModel<string>('notes', { required: true })
const { t } = useI18n()

const openNote = ref<string | null>(null)
</script>

<template>
  <div class="cart">
    <div v-if="!lines.length" class="empty">
      <PackageSearch :size="30" :stroke-width="1.3" />
      <p>
        {{ emptyText ?? (direct ? t('requests.direct.cartEmpty') : t('requests.new.cartEmpty')) }}
      </p>
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
                <MessageSquare :size="12" />
                <span>{{ line.note || t('requests.new.addNote') }}</span>
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
  </div>
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
}
.empty {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 32px 8px;
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
/* A link that looks like one: icon, accent colour, underline on hover. */
.note-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  justify-self: start;
  max-width: 100%;
  margin-top: 2px;
  padding: 0;
  border: 0;
  background: none;
  color: var(--ar-primary);
  font: inherit;
  font-size: 12px;
  text-align: left;
  cursor: pointer;
}
.note-link svg {
  flex: none;
}
.note-link span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.note-link:hover span {
  text-decoration: underline;
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
