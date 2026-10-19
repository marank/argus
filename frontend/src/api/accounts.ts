import type { Department, User } from '@/types/accounts'

import { createResource } from './resource'

export const usersApi = createResource<User>('/accounts/users')
export const departmentsApi = createResource<Department>('/accounts/departments')
