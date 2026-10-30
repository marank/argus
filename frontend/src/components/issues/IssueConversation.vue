<script setup lang="ts">
import { CircleCheck, RotateCcw, Send, Wrench } from '@lucide/vue'
import { NButton, NCard, NInput } from 'naive-ui'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/api/types'
import { useFormat } from '@/composables/useFormat'

/**
 * A report's conversation: the report itself, then messages and changes of status
 * in order. Messages of the viewer's side sit on the right, the other side's on
 * the left; IT and reporter keep their colour either way. Below, a field to write
 * and the status actions the viewer may take.
 */
const props = defineProps<{
  issue: Schemas['AssetIssueDetailOut']
  viewer: Schemas['IssueEntryOut']['side']
  /** Read-only roles see the conversation without the field. */
  canWrite: boolean
  busy: boolean
}>()
const emit = defineEmits<{
  send: [text: string]
  status: [status: Schemas['AssetIssueStatus'], text: string]
}>()
const { t } = useI18n()
const { dateTime, enumLabel } = useFormat()

const draft = ref('')

interface Message {
  type: 'message'
  key: string
  side: Schemas['IssueEntryOut']['side']
  name: string
  text: string
  at: string
  /** The report itself opens the conversation. */
  report?: boolean
}
interface StatusChange {
  type: 'status'
  key: string
  status: Schemas['AssetIssueStatus']
  name: string
  at: string
}

const items = computed<(Message | StatusChange)[]>(() => {
  const issue = props.issue
  const opening: Message = {
    type: 'message',
    key: 'report',
    side: 'reporter',
    name: issue.reported_by?.display_name ?? t('inventory.issues.detail.someone'),
    text: issue.description,
    at: issue.created_at,
    report: true,
  }
  return [
    opening,
    ...issue.entries.map((entry): Message | StatusChange => {
      const name = entry.author?.display_name ?? t('inventory.issues.detail.someone')
      return entry.kind === 'status'
        ? {
            type: 'status',
            key: entry.id,
            status: entry.status,
            name,
            at: entry.created_at,
          }
        : {
            type: 'message',
            key: entry.id,
            side: entry.side,
            name,
            text: entry.text,
            at: entry.created_at,
          }
    }),
  ]
})

const STATUS_ICONS = { open: RotateCcw, in_progress: Wrench, resolved: CircleCheck }

const initials = (name: string) =>
  name
    .split(/\s+/)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

function send() {
  const text = draft.value.trim()
  if (text) emit('send', text)
}
function changeStatus(status: Schemas['AssetIssueStatus']) {
  emit('status', status, draft.value.trim())
}
function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault()
    send()
  }
}

/** The parent clears the field once the message went through. */
defineExpose({ clear: () => (draft.value = '') })
</script>

<template>
  <NCard :title="t('inventory.issues.detail.conversation')" size="small">
    <ol class="conversation">
      <li v-for="item in items" :key="item.key">
        <div v-if="item.type === 'status'" class="status-line" :data-status="item.status">
          <component :is="STATUS_ICONS[item.status]" :size="14" />
          <span>{{ t(`inventory.issues.detail.event.${item.status}`, { name: item.name }) }}</span>
          <time class="mono">{{ dateTime(item.at) }}</time>
        </div>
        <div v-else class="message" :class="[item.side, { mine: item.side === viewer }]">
          <span class="avatar" aria-hidden="true">{{ initials(item.name) }}</span>
          <div class="bubble">
            <div class="meta">
              <strong>{{ item.name }}</strong>
              <span class="side">{{
                item.side === 'it'
                  ? t('inventory.issues.detail.it')
                  : t('inventory.issues.detail.reporter')
              }}</span>
              <time class="mono">{{ dateTime(item.at) }}</time>
            </div>
            <div v-if="item.report" class="report-kind eyebrow">
              {{ t('inventory.issues.detail.report') }} · {{ enumLabel('issueKind', issue.kind) }}
            </div>
            <p class="text">{{ item.text }}</p>
          </div>
        </div>
      </li>
    </ol>

    <template v-if="canWrite" #footer>
      <div class="composer">
        <NInput
          v-model:value="draft"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 8 }"
          :maxlength="4000"
          :placeholder="t('inventory.issues.detail.placeholder')"
          @keydown="onKeydown"
        />
        <div class="actions">
          <span class="muted small hint">{{ t('inventory.issues.detail.sendHint') }}</span>
          <div class="buttons">
            <template v-if="viewer === 'it'">
              <NButton
                v-if="issue.status === 'open'"
                :loading="busy"
                @click="changeStatus('in_progress')"
              >
                <template #icon><Wrench :size="15" /></template>
                {{ t('inventory.issues.startWork') }}
              </NButton>
              <NButton
                v-if="issue.status === 'resolved'"
                :loading="busy"
                @click="changeStatus('open')"
              >
                <template #icon><RotateCcw :size="15" /></template>
                {{ t('inventory.issues.reopen') }}
              </NButton>
            </template>
            <NButton
              v-if="issue.status !== 'resolved'"
              :loading="busy"
              :title="t('inventory.issues.detail.resolveHint')"
              @click="changeStatus('resolved')"
            >
              <template #icon><CircleCheck :size="15" /></template>
              {{ t('inventory.issues.resolve') }}
            </NButton>
            <NButton type="primary" :loading="busy" :disabled="!draft.trim()" @click="send">
              <template #icon><Send :size="15" /></template>
              {{ t('inventory.issues.detail.send') }}
            </NButton>
          </div>
        </div>
      </div>
    </template>
  </NCard>
</template>

<style scoped>
.conversation {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.message {
  --tone: var(--ar-text-muted);
  display: flex;
  align-items: flex-start;
  gap: 10px;
  /* The other side's messages leave room on the right, the viewer's on the left. */
  padding-right: 12%;
}
.message.mine {
  flex-direction: row-reverse;
  padding-right: 0;
  padding-left: 12%;
}
.message.it {
  --tone: var(--ar-primary);
}
.avatar {
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--tone) 45%, transparent);
  background: color-mix(in srgb, var(--tone) 14%, transparent);
  color: var(--tone);
  font-family: var(--ar-font-mono);
  font-size: 11px;
  font-weight: 700;
}
.bubble {
  min-width: 0;
  max-width: 100%;
  padding: 8px 12px 10px;
  border: 1px solid color-mix(in srgb, var(--tone) 30%, var(--ar-border));
  border-left: 3px solid var(--tone);
  border-radius: 4px;
  background: color-mix(in srgb, var(--tone) 6%, var(--ar-surface));
}
.mine .bubble {
  border-left-width: 1px;
  border-right: 3px solid var(--tone);
}
.meta {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 8px;
  font-size: 12px;
}
.side {
  padding: 0 6px;
  border-radius: 2px;
  background: color-mix(in srgb, var(--tone) 14%, transparent);
  color: var(--tone);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.meta time {
  color: var(--ar-text-subtle);
  font-size: 11px;
}
.report-kind {
  margin-top: 6px;
}
.text {
  margin: 4px 0 0;
  white-space: pre-line;
  overflow-wrap: anywhere;
}
.status-line {
  --tone: var(--ar-text-muted);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--tone);
  font-size: 12px;
}
.status-line[data-status='in_progress'] {
  --tone: var(--ar-info);
}
.status-line[data-status='resolved'] {
  --tone: var(--ar-success);
}
.status-line time {
  color: var(--ar-text-subtle);
  font-size: 11px;
}
.composer {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-left: auto;
}
@media (max-width: 640px) {
  .message,
  .message.mine {
    padding: 0;
  }
  .hint {
    display: none;
  }
}
</style>
