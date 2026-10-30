/**
 * Types generated from the backend's OpenAPI schema.
 *
 * `src/api/schema.d.ts` is written by `pnpm api:types` from `openapi.json` (VS Code task
 * "API: update types") and never edited by hand. The domain types in `src/types/` are
 * aliases of these, so a changed API shows up as a type error in the frontend.
 */
import type { components } from './schema'

export type Schemas = components['schemas']
