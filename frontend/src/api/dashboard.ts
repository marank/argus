import type {
  DueReturn,
  EmployeeOverview,
  ExpiringItem,
  ITOverview,
  LowStockItem,
  MyTasks,
  OpenOrder,
  OverdueReturn,
  TeamLoad,
  TrendWeek,
  UpcomingHandout,
  WaitingRequest,
} from '@/types/dashboard'

import { http } from './client'

export const dashboardApi = {
  it: () => http.get<ITOverview>('/dashboard/it'),
  me: () => http.get<EmployeeOverview>('/dashboard/me'),
  myTasks: () => http.get<MyTasks>('/dashboard/widgets/my-tasks'),
  overdueReturns: () => http.get<OverdueReturn[]>('/dashboard/widgets/overdue-returns'),
  teamLoad: () => http.get<TeamLoad>('/dashboard/widgets/team-load'),
  requestTrend: () => http.get<TrendWeek[]>('/dashboard/widgets/request-trend'),
  upcoming: (days: number) => http.get<UpcomingHandout[]>('/dashboard/widgets/upcoming', { days }),
  dueReturns: (days: number) => http.get<DueReturn[]>('/dashboard/widgets/due-returns', { days }),
  expiring: () => http.get<ExpiringItem[]>('/dashboard/widgets/expiring'),
  lowStock: () => http.get<LowStockItem[]>('/dashboard/widgets/low-stock'),
  openOrders: () => http.get<OpenOrder[]>('/dashboard/widgets/open-orders'),
  waitingRequests: () => http.get<WaitingRequest[]>('/dashboard/widgets/waiting-requests'),
}
