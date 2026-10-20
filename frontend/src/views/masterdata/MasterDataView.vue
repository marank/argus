<script setup lang="ts">
import { Lock } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import EmptyState from '@/components/common/EmptyState.vue'
import CrudPage from '@/components/crud/CrudPage.vue'
import { useAuthStore } from '@/stores/auth'
import NotFoundView from '@/views/NotFoundView.vue'

import { RESOURCES } from './resources'

const props = defineProps<{ resource: string }>()
const { t } = useI18n()
const auth = useAuthStore()
const definition = computed(() => RESOURCES[props.resource])

/** The user's roles must allow reading the records (roles themselves: administrators). */
const allowed = computed(() => {
  const def = definition.value
  if (!def) return false
  if (def.superuser) return auth.isSuperuser
  return !def.permission || auth.can(def.permission)
})
</script>

<template>
  <NotFoundView v-if="!definition" />
  <div v-else-if="!allowed" class="page">
    <EmptyState :icon="Lock" :text="t('masterdata.noAccess')" />
  </div>
  <CrudPage v-else :key="resource" :resource="definition" />
</template>
