import type {
  EmployeeOverview,
  ITOverview,
  MyTasks,
  OverdueReturn,
  TeamLoad,
  TrendWeek,
} from '@/types/dashboard'

import { http } from './client'

export const dashboardApi = {
  it: () => http.get<ITOverview>('/dashboard/it'),
  me: () => http.get<EmployeeOverview>('/dashboard/me'),
  myTasks: () => http.get<MyTasks>('/dashboard/widgets/my-tasks'),
  overdueReturns: () => http.get<OverdueReturn[]>('/dashboard/widgets/overdue-returns'),
  teamLoad: () => http.get<TeamLoad>('/dashboard/widgets/team-load'),
  requestTrend: () => http.get<TrendWeek[]>('/dashboard/widgets/request-trend'),
}
