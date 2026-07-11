<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getDocument, getErrorMessage, getHealth, getReviewResult, isNotFound, triggerReview } from '../api'
import KineticTitle from '../components/KineticTitle.vue'
import type { DocumentRecord, ReviewResult } from '../types/api'

const route = useRoute()
const documentId = Number(route.params.id)
const document = ref<DocumentRecord | null>(null)
const review = ref<ReviewResult | null>(null)
const loading = ref(true)
const reviewing = ref(false)
const error = ref('')
const llmProvider = ref('')
const severityRank = { high: 0, medium: 1, low: 2 }
const sortedItems = computed(() => [...(review.value?.items ?? [])].sort((a, b) => severityRank[a.severity] - severityRank[b.severity]))
const severityLabel = { high: '高风险', medium: '中风险', low: '低风险' }
const reviewProgressCopy = computed(() => {
  const prefix = llmProvider.value === 'deepseek' ? 'DeepSeek ' : llmProvider.value === 'mock' ? 'Mock 管线' : '审核管线'
  return `${prefix}正在检查合规风险、条款缺失、模糊表述、权益不对等和数据合规。`
})

async function load() {
  loading.value = true; error.value = ''
  try {
    const health = await getHealth().catch(() => null)
    llmProvider.value = health?.llm_provider.toLowerCase() ?? ''
    document.value = await getDocument(documentId)
    if (document.value.review_status !== 'pending') {
      try { review.value = await getReviewResult(documentId) } catch (reason) { if (!isNotFound(reason)) throw reason }
    }
  } catch (reason) { error.value = getErrorMessage(reason) } finally { loading.value = false }
}
async function runReview() {
  reviewing.value = true; error.value = ''
  try { review.value = await triggerReview(documentId); document.value = await getDocument(documentId) } catch (reason) { error.value = getErrorMessage(reason) } finally { reviewing.value = false }
}
onMounted(load)
</script>

<template>
  <section class="page-container">
    <div class="review-heading"><KineticTitle eyebrow="Review / Risk Map" title="审核结果" :description="document ? `${document.filename} · ${document.chunk_count} 个文本块` : '按风险等级浏览问题、原文和修改建议。'" /><div class="heading-actions"><RouterLink class="button" :to="`/documents/${documentId}/chat`">转到问答</RouterLink><button class="button button-primary" type="button" :disabled="reviewing || document?.status !== 'ready'" @click="runReview">{{ reviewing ? '审核中' : review ? '重新审核' : '发起审核' }}</button></div></div>
    <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
    <div v-if="loading" class="review-skeleton panel skeleton" aria-label="正在加载审核结果"></div>
    <div v-else-if="reviewing" class="review-progress panel" aria-live="polite"><div class="progress-copy"><span>ANALYZE</span><span>CLASSIFY</span><span>REPORT</span></div><h2>正在审核合同</h2><p>{{ reviewProgressCopy }}</p></div>
    <div v-else-if="!review" class="empty-review panel"><span>NO REVIEW YET</span><h2>这份文档还没有审核记录</h2><p>发起审核后，风险卡片、原文和修改建议会出现在这里。</p><button class="button button-primary" type="button" @click="runReview">开始第一次审核</button></div>
    <template v-else>
      <div class="metric-grid" aria-label="审核统计"><article class="metric panel"><span>问题总数</span><strong>{{ review.total_items }}</strong></article><article class="metric panel danger"><span>高风险</span><strong>{{ review.risk_count }}</strong></article><article class="metric panel"><span>耗时</span><strong>{{ review.duration_ms }}<small>ms</small></strong></article></div>
      <article class="summary-card panel"><span>EXECUTIVE SUMMARY</span><p>{{ review.summary }}</p></article>
      <div class="risk-list">
        <article v-for="item in sortedItems" :key="item.id" class="risk-card panel" :class="`risk-${item.severity}`">
          <div class="risk-head"><div><span class="severity" :class="item.severity">{{ severityLabel[item.severity] }}</span><span class="category">{{ item.category }}</span></div><span class="risk-id">R-{{ String(item.id).padStart(3, '0') }}</span></div>
          <h2>{{ item.title }}</h2><p class="description">{{ item.description }}</p>
          <blockquote><span>原文证据</span>“{{ item.source_text }}”</blockquote>
          <div class="suggestion"><span>修改建议</span><p>{{ item.suggestion }}</p></div>
        </article>
      </div>
    </template>
  </section>
</template>

<style scoped>
.review-heading { display: flex; align-items: end; justify-content: space-between; gap: 24px; }.heading-actions { display: flex; flex-wrap: wrap; gap: 8px; }.review-skeleton { height: 420px; margin-top: 36px; }.empty-review, .review-progress { margin-top: 36px; padding: 64px 28px; text-align: center; }.empty-review > span { color: var(--accent); font-family: "Cascadia Code", monospace; font-size: 11px; letter-spacing: .15em; }.empty-review p, .review-progress p { margin: 8px auto 24px; color: var(--muted); }.progress-copy { display: flex; justify-content: center; gap: 18px; color: var(--accent); font-family: "Cascadia Code", monospace; font-size: 11px; letter-spacing: .12em; }.progress-copy span { animation: word-pulse 1.2s ease-in-out infinite; }.progress-copy span:nth-child(2) { animation-delay: 160ms; }.progress-copy span:nth-child(3) { animation-delay: 320ms; }@keyframes word-pulse { 0%, 70%, 100% { opacity: .3; transform: translateY(0); } 35% { opacity: 1; transform: translateY(-3px); } }.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 36px; }.metric { padding: 18px; }.metric span { color: var(--muted); font-size: 12px; }.metric strong { display: block; margin-top: 8px; font-size: 32px; font-variant-numeric: tabular-nums; animation: metric-enter 320ms ease-out both; }.metric strong small { margin-left: 3px; color: var(--muted); font-size: 12px; }.metric.danger strong { color: #ff938d; }.metric .pipeline { color: var(--accent); font-family: "Cascadia Code", monospace; font-size: 20px; }@keyframes metric-enter { from { opacity: 0; transform: translateY(8px); } }.summary-card { margin-top: 16px; border-left: 3px solid var(--accent); padding: 24px; }.summary-card span, .suggestion > span, blockquote span { display: block; margin-bottom: 8px; color: var(--accent); font-family: "Cascadia Code", monospace; font-size: 10px; font-weight: 700; letter-spacing: .14em; }.summary-card p { margin: 0; font-size: 17px; line-height: 1.7; }.risk-list { display: grid; gap: 16px; margin-top: 24px; }.risk-card { border-left-width: 4px; padding: 24px; }.risk-high { border-left-color: var(--danger); }.risk-medium { border-left-color: var(--warning); }.risk-low { border-left-color: var(--accent); }.risk-head { display: flex; justify-content: space-between; gap: 16px; }.severity, .category { display: inline-flex; min-height: 28px; align-items: center; border: 1px solid var(--border); border-radius: 999px; padding: 0 10px; font-size: 12px; font-weight: 700; }.severity { margin-right: 8px; }.severity.high { border-color: rgba(248, 81, 73, .45); color: #ff938d; }.severity.medium { border-color: rgba(210, 153, 34, .45); color: #e3b341; }.severity.low { border-color: rgba(88, 166, 255, .45); color: #79b8ff; }.risk-id { color: var(--muted); font-family: "Cascadia Code", monospace; font-size: 11px; }.risk-card h2 { margin: 20px 0 8px; font-size: 20px; }.description { color: var(--muted); line-height: 1.65; }blockquote { margin: 20px 0 0; border: 1px solid var(--border); border-radius: 10px; background: var(--bg); padding: 16px; color: #c9d1d9; font-style: italic; line-height: 1.6; }.suggestion { margin-top: 14px; border-radius: 10px; background: rgba(63, 185, 80, .07); padding: 16px; }.suggestion > span { color: #72d57d; }.suggestion p { margin: 0; line-height: 1.6; }
@media (max-width: 840px) { .review-heading { align-items: flex-start; flex-direction: column; }.metric-grid { grid-template-columns: repeat(2, 1fr); } }.heading-actions .button { flex: 1; }
@media (max-width: 480px) { .metric-grid { grid-template-columns: 1fr; }.risk-head { flex-direction: column; }.risk-card { padding: 19px; } }
@media (prefers-reduced-motion: reduce) { .progress-copy span, .metric strong { animation: none; } }
.heading-actions { max-width: 100%; }
.heading-actions .button { flex: 0 0 auto; }
.metric-grid { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
</style>
