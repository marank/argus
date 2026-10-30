import type { Schemas } from '@/api/types'
import type { Id } from '@/types/common'

import { http } from './client'
import { createResource } from './resource'

export const usersApi = {
  ...createResource<Schemas['UserOut']>('/accounts/users'),
  /** For users who lost their phone and backup codes. */
  resetTwoFactor: (id: Id) =>
    http.post<Schemas['UserOut']>(`/accounts/users/${id}/two-factor/reset`),
}
export const departmentsApi = createResource<Schemas['DepartmentOut']>('/accounts/departments')
export const teamsApi = createResource<Schemas['TeamOut']>('/accounts/teams')
export const rolesApi = {
  ...createResource<Schemas['RoleOut']>('/accounts/roles'),
  /** The areas a role can grant, in the order of the role editor. */
  resources: () => http.get<Schemas['ResourceOut'][]>('/accounts/roles/resources'),
}
