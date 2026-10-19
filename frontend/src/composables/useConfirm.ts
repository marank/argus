import { useDialog } from 'naive-ui'
import { useI18n } from 'vue-i18n'

/** Promise-based confirmation dialog. */
export function useConfirm() {
  const dialog = useDialog()
  const { t } = useI18n()

  return (content: string, options: { danger?: boolean; positiveText?: string } = {}) =>
    new Promise<boolean>((resolve) => {
      const show = options.danger ? dialog.error : dialog.warning
      show({
        title: t('common.confirmTitle'),
        content,
        positiveText: options.positiveText ?? t('common.confirm'),
        negativeText: t('common.cancel'),
        onPositiveClick: () => resolve(true),
        onNegativeClick: () => resolve(false),
        onClose: () => resolve(false),
        onMaskClick: () => resolve(false),
      })
    })
}
