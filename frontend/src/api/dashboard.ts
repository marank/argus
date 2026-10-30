import type { Schemas } from '@/api/types'

import { http } from './client'

export const dashboardApi = {
  it: () => http.get<Schemas['ITOverviewOut']>('/dashboard/it'),
  me: () => http.get<Schemas['EmployeeOverviewOut']>('/dashboard/me'),
  myTasks: () => http.get<Schemas['MyTasksOut']>('/dashboard/widgets/my-tasks'),
  overdueReturns: () =>
    http.get<Schemas['OverdueReturnOut'][]>('/dashboard/widgets/overdue-returns'),
  teamLoad: () => http.get<Schemas['TeamLoadOut']>('/dashboard/widgets/team-load'),
  requestTrend: () => http.get<Schemas['TrendWeekOut'][]>('/dashboard/widgets/request-trend'),
  upcoming: (days: number) =>
    http.get<Schemas['UpcomingOut'][]>('/dashboard/widgets/upcoming', { days }),
  dueReturns: (days: number) =>
    http.get<Schemas['DueReturnOut'][]>('/dashboard/widgets/due-returns', { days }),
  expiring: () => http.get<Schemas['ExpiringOut'][]>('/dashboard/widgets/expiring'),
  lowStock: () => http.get<Schemas['LowStockOut'][]>('/dashboard/widgets/low-stock'),
  openOrders: () => http.get<Schemas['OpenOrderOut'][]>('/dashboard/widgets/open-orders'),
  waitingRequests: () =>
    http.get<Schemas['WaitingRequestOut'][]>('/dashboard/widgets/waiting-requests'),
}
