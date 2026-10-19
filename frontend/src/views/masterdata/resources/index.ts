import type { ResourceDef } from '@/components/crud/types'

import categories from './categories'
import departments from './departments'
import locations from './locations'
import manufacturers from './manufacturers'
import models from './models'
import numberSequences from './numberSequences'
import suppliers from './suppliers'
import teams from './teams'
import users from './users'

/* eslint-disable @typescript-eslint/no-explicit-any */
export const RESOURCES: Record<string, ResourceDef<any>> = {
  models,
  categories,
  manufacturers,
  suppliers,
  locations,
  departments,
  teams,
  users,
  numberSequences,
}
