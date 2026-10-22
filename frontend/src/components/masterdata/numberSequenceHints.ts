import { h, type Component, type FunctionalComponent } from 'vue'

import NumberSequenceHints from './NumberSequenceHints.vue'

/**
 * NumberSequenceHints as a form section's `extra`, suggesting the sequence of the category in the
 * form field `from`. Without declared props, everything the drawer passes (form, row, readonly,
 * the set listener) arrives as props and is handed on.
 */
export const numberSequenceHints =
  (from: 'parent' | 'category'): FunctionalComponent =>
  (props) =>
    h(NumberSequenceHints as Component, { ...props, from })
