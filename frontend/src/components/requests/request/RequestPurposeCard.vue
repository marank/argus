<script setup lang="ts">
import { Target } from '@lucide/vue'
import { NInput } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import { usersApi } from '@/api/accounts'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'

import type { RequestDetails } from './types'

/** What the request is for and, for IT recording it for someone, who it is for. */
defineProps<{
  canChooseRequester: boolean
  requesterPlaceholder?: string
  /** Shown in the picker before its list is loaded, e.g. when asking again. */
  initialRequester?: Schemas['UserRefOut'] | null
  /** Only the fields, as part of a card around it (no frame, no title). */
  plain?: boolean
}>()
const details = defineModel<RequestDetails>({ required: true })
const { t } = useI18n()
</script>

<template>
  <section class="purpose" :class="{ plain }">
    <header v-if="!plain">
      <Target :size="16" />
      <h2>{{ t('requests.new.purposeTitle') }}</h2>
    </header>
    <div class="fields">
      <div class="field">
        <FieldLabel :label="t('requests.purpose')" required />
        <NInput v-model:value="details.title" :placeholder="t('requests.purposePlaceholder')" />
      </div>
      <div v-if="canChooseRequester" class="field">
        <FieldLabel :label="t('requests.requestedFor')" />
        <EntitySelect
          v-model="details.requester"
          :fetcher="usersApi.list"
          :params="{ is_active: true, is_terminal: false }"
          :label="(u) => u.display_name"
          :initial="(initialRequester ?? null) as never"
          :placeholder="requesterPlaceholder"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
/* Like the period card next to it. */
.purpose {
  display: grid;
  gap: 14px;
  padding: 16px 18px 18px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
.purpose.plain {
  padding: 0;
  border: none;
  background: none;
}
header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ar-text-muted);
}
h2 {
  margin: 0;
  color: var(--ar-text);
  font-size: 14px;
  font-weight: 600;
}
.fields {
  display: grid;
  gap: 12px;
}
.field {
  display: grid;
  gap: 4px;
}
</style>
