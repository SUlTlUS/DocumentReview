<script setup lang="ts">
const props = defineProps<{ eyebrow: string; title: string; description?: string }>()
const characters = Array.from(props.title)
</script>

<template>
  <header class="kinetic-header">
    <p class="kinetic-eyebrow">{{ eyebrow }}</p>
    <h1 :aria-label="title">
      <span v-for="(character, index) in characters" :key="`${character}-${index}`" class="kinetic-character" aria-hidden="true" :style="{ '--character-index': index }">
        {{ character === ' ' ? '\u00A0' : character }}
      </span>
    </h1>
    <p v-if="description" class="kinetic-description">{{ description }}</p>
  </header>
</template>

<style scoped>
.kinetic-header { max-width: 780px; }
.kinetic-eyebrow { margin: 0 0 12px; color: var(--accent); font-family: "Cascadia Code", Consolas, monospace; font-size: 12px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; }
h1 { margin: 0; font-size: clamp(2.2rem, 6vw, 4.8rem); font-weight: 780; letter-spacing: -0.055em; line-height: 0.98; }
.kinetic-character { display: inline-block; animation: character-enter 420ms cubic-bezier(0.16, 1, 0.3, 1) both; animation-delay: calc(var(--character-index) * 22ms); }
.kinetic-description { max-width: 640px; margin: 20px 0 0; color: var(--muted); font-size: 16px; line-height: 1.7; }
@keyframes character-enter { from { opacity: 0; transform: translateY(0.55em) rotate(2deg); } to { opacity: 1; transform: translateY(0) rotate(0); } }
@media (prefers-reduced-motion: reduce) { .kinetic-character { animation: none; } }
</style>
