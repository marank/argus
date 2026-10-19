import type { EmployeeOverview, ITOverview } from '@/types/dashboard'

import { http } from './client'

export const dashboardApi = {
  it: () => http.get<ITOverview>('/dashboard/it'),
  me: () => http.get<EmployeeOverview>('/dashboard/me'),
}
