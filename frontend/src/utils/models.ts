import type { AssetModelRef } from '@/types/masterdata'

/**
 * "Scanova 4-slot cradle (CRD-SX5X-4SC)": the manufacturer's designation tells apart
 * models that share a name. Left out where it just repeats the name.
 */
export function modelLabel(
  model: Pick<AssetModelRef, 'name' | 'full_name'> & { designation?: string },
) {
  const { designation } = model
  return designation && designation !== model.name
    ? `${model.full_name} (${designation})`
    : model.full_name
}
