<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { getHealth } from './api'
import type { HealthStatus } from './types/api'

const health = ref<HealthStatus | null>(null)
const healthFailed = ref(false)
const environmentLabel = computed(() => {
  if (healthFailed.value) return '后端未连接'
  if (!health.value) return '检查审核环境…'
  if (health.value.llm_provider.toLowerCase() !== 'deepseek') return 'Mock 审核环境'
  return health.value.deepseek_api_configured ? 'DeepSeek API 已配置' : 'DeepSeek API 未配置'
})
const environmentState = computed(() => {
  if (healthFailed.value || (health.value?.llm_provider.toLowerCase() === 'deepseek' && !health.value.deepseek_api_configured)) return 'warning'
  return health.value ? 'ready' : 'loading'
})

onMounted(async () => {
  try { health.value = await getHealth() } catch { healthFailed.value = true }
})
</script>

<template>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <div class="app-shell">
    <aside class="sidebar" aria-label="主导航">
      <RouterLink class="brand" to="/documents" aria-label="RAG 文档审核首页">
        <span class="brand-mark" aria-hidden="true">RD</span>
        <span>
          <strong>Document Review</strong>
          <small>RAG LEGAL DESK</small>
        </span>
      </RouterLink>
      <nav class="nav-list">
        <RouterLink to="/documents"><span class="nav-index">01</span><span>文档列表</span></RouterLink>
        <RouterLink to="/upload"><span class="nav-index">02</span><span>上传文档</span></RouterLink>
      </nav>
      <div class="sidebar-foot" role="status" aria-live="polite">
        <span class="status-dot" :class="`status-dot--${environmentState}`" aria-hidden="true"></span>
        <span>{{ environmentLabel }}</span>
      </div>
    </aside>
    <main id="main-content" class="main-content" tabindex="-1">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in"><component :is="Component" /></Transition>
      </RouterView>
    </main>
  </div>
</template>
