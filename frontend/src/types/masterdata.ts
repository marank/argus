import type { Schemas } from '@/api/types'
import { allValues } from '@/utils/enums'

export const CATEGORY_KINDS = allValues<Schemas['CategoryKind']>({
  hardware: true,
  software: true,
})
