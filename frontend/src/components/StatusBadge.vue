<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()
const labels: Record<string, string> = {
  uploaded: '已上传', parsing: '解析中', ready: '就绪', parse_failed: '解析失败',
  pending: '待审核', reviewing: '审核中', completed: '已审核', review_failed: '审核失败',
}
const label = computed(() => labels[props.status] ?? props.status)
</script>

<template><span class="status-badge" :class="`status-${status}`"><span class="badge-dot" aria-hidden="true"></span>{{ label }}</span></template>

<style scoped>
.status-badge { display: inline-flex; min-height: 28px; align-items: center; gap: 7px; border: 1px solid var(--border); border-radius: 999px; padding: 0 10px; color: var(--muted); font-size: 12px; font-weight: 700; }
.badge-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.status-ready, .status-completed { border-color: rgba(63, 185, 80, 0.35); color: #72d57d; }
.status-parsing { border-color: rgba(88, 166, 255, 0.4); color: #79b8ff; }
.status-reviewing { border-color: rgba(210, 153, 34, 0.4); color: #e3b341; }
.status-parse_failed, .status-review_failed { border-color: rgba(248, 81, 73, 0.4); color: #ff938d; }
</style>
