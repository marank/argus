import type { Department, Team, User } from '@/types/accounts'

import type { Id } from '@/types/common'

import { http } from './client'
import { createResource } from './resource'

export const usersApi = {
  ...createResource<User>('/accounts/users'),
  /** For users who lost their phone and backup codes. */
  resetTwoFactor: (id: Id) => http.post<User>(`/accounts/users/${id}/two-factor/reset`),
}
export const departmentsApi = createResource<Department>('/accounts/departments')
export const teamsApi = createResource<Team>('/accounts/teams')
