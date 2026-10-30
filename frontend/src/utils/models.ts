import type { Schemas } from '@/api/types'

/**
 * "Scanova 4-slot cradle (CRD-SX5X-4SC)": the manufacturer's designation tells apart
 * models that share a name. Left out where it just repeats the name.
 */
export function modelLabel(
  model: Pick<Schemas['AssetModelRefOut'], 'name' | 'full_name'> & { designation?: string },
) {
  const { designation } = model
  return designation && designation !== model.name
    ? `${model.full_name} (${designation})`
    : model.full_name
}
