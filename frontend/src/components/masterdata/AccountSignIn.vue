<script setup lang="ts">
import type { Schemas } from '@/api/types'

import PasswordSet from './PasswordSet.vue'
import TwoFactorReset from './TwoFactorReset.vue'

/** Sign-in of an employee in the edit drawer: password (local accounts) and two-factor state. */
defineProps<{
  form: Record<string, unknown>
  row?: Schemas['UserOut'] | null
  readonly?: boolean
}>()
</script>

<template>
  <PasswordSet :row="row" :readonly="readonly" />
  <TwoFactorReset :form="form" :row="row" :readonly="readonly" />
</template>
