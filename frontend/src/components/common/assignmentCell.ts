import type { Schemas } from '@/api/types'
import { NTag } from 'naive-ui'
import { h } from 'vue'

/** Table cell "Responsible": team tag with the assignee below, or a dash. */
export function assignmentCell(row: {
  assigned_team: Schemas['TeamRefOut'] | null
  assignee: Schemas['UserRefOut'] | null
}) {
  if (!row.assigned_team && !row.assignee) return h('span', { class: 'muted' }, '—')
  return h('div', { class: 'assignment-cell' }, [
    row.assigned_team
      ? h(NTag, { size: 'small', bordered: false }, () => row.assigned_team!.name)
      : null,
    row.assignee
      ? h('small', { style: 'display:block;margin-top:2px' }, row.assignee.display_name)
      : null,
  ])
}
