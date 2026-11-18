import type { Schemas } from '@/api/types'
import type { ListParams, Page } from '@/types/common'

import { http } from './client'

export const activityApi = {
  list: (params: ListParams = {}) => http.get<Page<Schemas['ActivityOut']>>('/activities', params),
}
