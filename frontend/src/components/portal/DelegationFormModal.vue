<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { NAlert, NButton, NFormItem, NModal } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import { delegationsApi } from '@/api/requests'
import DateField from '@/components/common/DateField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { toIsoDate } from '@/composables/useFormat'
import type { Id, ListParams } from '@/types/common'

/** Names a delegate, or changes the period of one (`entry`). */
const props = defineProps<{ entry?: Schemas['ApprovalDelegationOut'] | null }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [] }>()
const { t } = useI18n()

const DAY = 86_400_000
const startOfToday = () => new Date().setHours(0, 0, 0, 0)
const fromIso = (value: string) => new Date(`${value}T00:00:00`).getTime()

const delegate = ref<Id | null>(null)
const startsOn = ref<number | null>(null)
const endsOn = ref<number | null>(null)
const error = ref('')
const busy = ref(false)

const editing = computed(() => !!props.entry)
// Once a delegate has started, only the end can change.
const started = computed(() => props.entry?.status === 'running')

watch(show, (visible) => {
  if (!visible) return
  error.value = ''
  delegate.value = props.entry?.delegate.id ?? null
  startsOn.value = props.entry ? fromIso(props.entry.starts_on) : startOfToday()
  endsOn.value = props.entry?.ends_on ? fromIso(props.entry.ends_on) : null
})

// The server needs at least two characters; the select also loads once with none.
const candidates = async (params: ListParams) => {
  const q = String(params.q ?? '').trim()
  const items = q.length < 2 ? [] : await delegationsApi.candidates(q)
  return { items, count: items.length }
}
const beforeToday = (day: number) => day < startOfToday()
const beforeStart = (day: number) => day < Math.max(startsOn.value ?? 0, startOfToday())

/** Quick choices for the end: the start (or today) plus a number of weeks, or open. */
function endAfterWeeks(weeks: number) {
  const from = Math.max(startsOn.value ?? startOfToday(), startOfToday())
  endsOn.value = from + (weeks * 7 - 1) * DAY
}

const ready = computed(() => !!delegate.value && !!startsOn.value)

async function save() {
  if (!ready.value) return
  error.value = ''
  busy.value = true
  const period = { starts_on: toIsoDate(startsOn.value)!, ends_on: toIsoDate(endsOn.value) }
  try {
    if (props.entry) await delegationsApi.changePeriod(props.entry.id, period)
    else await delegationsApi.add({ delegate: delegate.value as string, ...period })
    show.value = false
    emit('saved')
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="editing ? t('requests.delegations.edit') : t('requests.delegations.add')"
    style="max-width: 480px"
  >
    <form @submit.prevent="save">
      <p class="muted text">
        {{ editing ? t('requests.delegations.editText') : t('requests.delegations.addText') }}
      </p>
      <NAlert v-if="error" type="error" :bordered="false" class="alert">{{ error }}</NAlert>
      <NFormItem :label="t('requests.delegations.delegate')">
        <strong v-if="entry">{{ entry.delegate.display_name }}</strong>
        <EntitySelect
          v-else
          v-model="delegate"
          :fetcher="candidates"
          :label="(u: Schemas['UserRefOut']) => u.display_name"
          :placeholder="t('requests.delegations.search')"
        />
      </NFormItem>
      <div class="dates">
        <NFormItem :label="t('requests.delegations.from')">
          <DateField
            v-model:value="startsOn"
            :disabled="started"
            :is-date-disabled="beforeToday"
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem :label="t('requests.delegations.until')">
          <DateField
            v-model:value="endsOn"
            clearable
            :is-date-disabled="beforeStart"
            :placeholder="t('requests.delegations.untilRemoved')"
            style="width: 100%"
          />
        </NFormItem>
      </div>
      <div class="quick">
        <span class="muted">{{ t('requests.delegations.quick') }}</span>
        <NButton size="tiny" secondary @click="endAfterWeeks(1)">
          {{ t('requests.delegations.weeks', 1) }}
        </NButton>
        <NButton size="tiny" secondary @click="endAfterWeeks(2)">
          {{ t('requests.delegations.weeks', 2) }}
        </NButton>
        <NButton size="tiny" secondary @click="endAfterWeeks(3)">
          {{ t('requests.delegations.weeks', 3) }}
        </NButton>
        <NButton size="tiny" secondary @click="endsOn = null">
          {{ t('requests.delegations.untilRemoved') }}
        </NButton>
      </div>
      <p v-if="started" class="muted hint">{{ t('requests.delegations.startedHint') }}</p>
      <div class="row actions">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" attr-type="submit" :disabled="!ready" :loading="busy">
          {{ editing ? t('common.save') : t('requests.delegations.save') }}
        </NButton>
      </div>
    </form>
  </NModal>
</template>

<style scoped>
.text {
  margin: 0 0 14px;
  line-height: 1.5;
}
.alert {
  margin-bottom: 12px;
}
.dates {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
}
.quick {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: -6px;
  font-size: 12px;
}
.hint {
  margin: 10px 0 0;
  font-size: 12px;
}
.actions {
  justify-content: flex-end;
  margin-top: 18px;
}
@media (max-width: 520px) {
  .dates {
    grid-template-columns: 1fr;
  }
}
</style>
