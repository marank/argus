<script setup lang="ts">
import { Mail, Phone } from '@lucide/vue'
import { NCard } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/api/types'
import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'

/** For IT: how to reach the reporter beyond a message, e.g. to arrange a swap. */
const props = defineProps<{
  reporter: NonNullable<Schemas['AssetIssueDetailOut']['reported_by']>
}>()
const { t } = useI18n()

const entries = computed<DetailEntry[]>(() => [
  { label: t('inventory.issues.detail.jobTitle'), value: props.reporter.job_title },
  { label: t('inventory.issues.detail.department'), value: props.reporter.department },
  { label: t('inventory.issues.detail.email'), slot: 'email', wide: true },
  { label: t('inventory.issues.detail.phone'), slot: 'phone' },
])
</script>

<template>
  <NCard :title="t('inventory.issues.detail.contact')" size="small">
    <div class="stack">
      <strong>{{ reporter.display_name }}</strong>
      <DetailGrid :entries="entries">
        <template #email>
          <a v-if="reporter.email" :href="`mailto:${reporter.email}`" class="contact">
            <Mail :size="13" /> {{ reporter.email }}
          </a>
          <template v-else>—</template>
        </template>
        <template #phone>
          <a v-if="reporter.phone" :href="`tel:${reporter.phone}`" class="contact mono">
            <Phone :size="13" /> {{ reporter.phone }}
          </a>
          <template v-else>—</template>
        </template>
      </DetailGrid>
    </div>
  </NCard>
</template>

<style scoped>
.contact {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  overflow-wrap: anywhere;
}
</style>
