import type { Schemas } from '@/api/types'
import { allValues } from '@/utils/enums'

export const CATEGORY_KINDS = allValues<Schemas['CategoryKind']>({
  hardware: true,
  software: true,
})

export const MODEL_CHOICES = allValues<Schemas['ModelChoice']>({
  any_or_specific: true,
  any_only: true,
  specific_only: true,
})
