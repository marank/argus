import type { Department, Team, User } from '@/types/accounts'

import { createResource } from './resource'

export const usersApi = createResource<User>('/accounts/users')
export const departmentsApi = createResource<Department>('/accounts/departments')
export const teamsApi = createResource<Team>('/accounts/teams')
