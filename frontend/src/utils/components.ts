import { componentTypesApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import type { Id } from '@/types/common'

/**
 * The tracked parts devices of a category have, e.g. the battery. Without them the forms
 * still work (the parts just do not show), so a failed request leaves the list empty.
 */
export async function loadComponentTypes(
  category: Id | null | undefined,
): Promise<Schemas['ComponentTypeOut'][]> {
  if (!category) return []
  try {
    return (await componentTypesApi.list({ category, page_size: 50 })).items
  } catch {
    return []
  }
}
