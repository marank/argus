import type { Schemas } from '@/api/types'
import { useMessage } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import { requestsApi } from '@/api/requests'
import { useConfirm } from '@/composables/useConfirm'

/**
 * Emails an employee to return their devices, after asking (as on the
 * request's page); `sending` is the request being reminded, `reload` runs after.
 */
export function useRemind(reload: () => Promise<unknown>) {
  const { t } = useI18n()
  const message = useMessage()
  const confirm = useConfirm()
  const sending = ref<string | null>(null)

  async function remind(row: Pick<Schemas['OverdueReturnOut'], 'id' | 'requester'>) {
    const name = row.requester.display_name
    if (!(await confirm(t('requests.actions.confirmRemind', { name })))) return
    sending.value = row.id
    try {
      await requestsApi.remind(row.id)
      message.success(t('requests.actions.remindSent', { name }))
      await reload()
    } catch (error) {
      message.error(error instanceof ApiError ? error.message : t('common.error'))
    } finally {
      sending.value = null
    }
  }

  return { remind, sending }
}
