<script setup lang="ts">
// The ARGUS wordmark (design/logo/wordmark-argus.svg), sized by its cap height and
// drawn in the current text colour, so it follows light and dark like the text did.
const props = defineProps<{ height: number }>()
const width = Math.round((props.height * 3553) / 700)
</script>

<template>
  <svg
    viewBox="0 0 3553 700"
    :width="width"
    :height="height"
    role="img"
    aria-label="Argus"
    class="wordmark"
  >
    <g fill="currentColor" transform="translate(-10 700) scale(1 -1)">
      <path d="M264 700H374L627 0H509L449 166H188L128 0H10ZM422 263 319 559H317L216 263Z" />
      <path
        transform="translate(717 0)"
        d="M602 226V0H486V198L414 277H186V0H70V700H496L598 597V382L525 309ZM186 373H444L484 413V562L444 602H186Z"
      />
      <path
        transform="translate(1464 0)"
        d="M60 113V587L173 700H507L618 589V497H502V548L449 600H233L176 544V156L233 100H449L505 155V282H352V382H618V113L505 0H173Z"
      />
      <path
        transform="translate(2212 0)"
        d="M70 117V700H186V156L243 100H449L506 156V700H622V117L505 0H187Z"
      />
      <path
        transform="translate(2984 0)"
        d="M55 103V191H169V138L207 100H425L465 140V269L426 308H160L57 410V597L160 700H468L571 597V508H457V562L418 600H210L171 562V446L210 408H476L579 305V105L474 0H158Z"
      />
    </g>
  </svg>
</template>

<style scoped>
.wordmark {
  flex-shrink: 0;
}
</style>
