<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { deleteDocument, getDocuments, getErrorMessage } from '../api'
import KineticTitle from '../components/KineticTitle.vue'
import StatusBadge from '../components/StatusBadge.vue'
import type { DocumentRecord } from '../types/api'

const documents = ref<DocumentRecord[]>([])
const loading = ref(true)
const error = ref('')
const deletingId = ref<number | null>(null)
const formatSize = (bytes: number) => bytes < 1024 ? `${bytes} B` : bytes < 1024 ** 2 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 ** 2).toFixed(1)} MB`
const formatDate = (value: string) => new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))

async function loadDocuments() {
  loading.value = true; error.value = ''
  try { documents.value = (await getDocuments()).items } catch (reason) { error.value = getErrorMessage(reason) } finally { loading.value = false }
}
async function remove(document: DocumentRecord) {
  if (!window.confirm(`确定删除“${document.filename}”及其审核和问答数据吗？`)) return
  deletingId.value = document.id
  try { await deleteDocument(document.id); documents.value = documents.value.filter(item => item.id !== document.id) } catch (reason) { error.value = getErrorMessage(reason) } finally { deletingId.value = null }
}
onMounted(loadDocuments)
</script>

<template>
  <section class="page-container">
    <div class="list-heading"><KineticTitle eyebrow="Workspace / 01" title="文档列表" description="按上传时间查看全部合同，解析、审核和问答状态一目了然。" /><RouterLink class="button button-primary" to="/upload">上传新文档</RouterLink></div>
    <div v-if="error" class="error-banner" role="alert">{{ error }} <button class="retry" type="button" @click="loadDocuments">重试</button></div>
    <div v-if="loading" class="document-grid" aria-label="正在加载文档"><div v-for="index in 3" :key="index" class="document-card panel skeleton"></div></div>
    <div v-else-if="documents.length === 0" class="empty-state panel"><span>NO DOCUMENTS</span><h2>尚未上传文档</h2><p>从一份 PDF、DOCX 或 TXT 合同开始。</p><RouterLink class="button button-primary" to="/upload">上传第一份文档</RouterLink></div>
    <div v-else class="document-grid">
      <article v-for="document in documents" :key="document.id" class="document-card panel">
        <div class="document-sequence" aria-hidden="true">{{ String(document.id).padStart(2, '0') }}</div>
        <div class="document-main"><div class="document-name"><span class="file-type">{{ document.file_type.toUpperCase() }}</span><h2>{{ document.filename }}</h2></div><p>{{ document.content_summary || '暂无内容摘要' }}</p><div class="document-meta"><span>{{ formatSize(document.file_size) }}</span><span>{{ document.chunk_count }} chunks</span><time :datetime="document.upload_time">{{ formatDate(document.upload_time) }}</time></div></div>
        <div class="document-state"><StatusBadge :status="document.status" /><StatusBadge :status="document.review_status" /></div>
        <div class="document-actions">
          <RouterLink class="button" :to="`/documents/${document.id}/review`">审核</RouterLink>
          <RouterLink class="button" :to="`/documents/${document.id}/chat`">问答</RouterLink>
          <button class="button button-danger" type="button" :disabled="deletingId === document.id" @click="remove(document)">{{ deletingId === document.id ? '删除中' : '删除' }}</button>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.list-heading { display: flex; align-items: end; justify-content: space-between; gap: 24px; }.document-grid { display: grid; gap: 16px; margin-top: 36px; }.document-card { position: relative; display: grid; grid-template-columns: 56px 1fr auto; gap: 20px; min-height: 184px; padding: 24px; transition: border-color 180ms ease-out, transform 180ms ease-out; }.document-card:hover { border-color: rgba(88, 166, 255, .45); transform: translateY(-2px); }.document-sequence { color: var(--border); font-size: 34px; font-weight: 800; line-height: 1; }.document-name { display: flex; align-items: center; gap: 10px; }.document-name h2 { margin: 0; font-size: 18px; }.file-type { border: 1px solid var(--border); border-radius: 6px; padding: 3px 6px; color: var(--accent); font-family: "Cascadia Code", monospace; font-size: 10px; }.document-main p { display: -webkit-box; overflow: hidden; margin: 14px 0; color: var(--muted); line-height: 1.55; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }.document-meta { display: flex; flex-wrap: wrap; gap: 14px; color: var(--muted); font-family: "Cascadia Code", monospace; font-size: 11px; }.document-state { display: flex; align-items: flex-start; gap: 8px; }.document-actions { display: flex; grid-column: 2 / -1; gap: 8px; }.document-actions .button { min-height: 38px; }.empty-state { margin-top: 36px; padding: 64px 24px; text-align: center; }.empty-state span { color: var(--accent); font-family: "Cascadia Code", monospace; font-size: 11px; letter-spacing: .16em; }.empty-state h2 { margin-bottom: 8px; }.empty-state p { margin: 0 0 24px; color: var(--muted); }.skeleton { height: 184px; }.retry { border: 0; background: transparent; color: var(--accent); cursor: pointer; font-weight: 700; text-decoration: underline; }
@media (max-width: 840px) { .list-heading { align-items: flex-start; flex-direction: column; }.document-card { grid-template-columns: 1fr; }.document-sequence { display: none; }.document-state, .document-actions { grid-column: 1; flex-wrap: wrap; } }
@media (prefers-reduced-motion: reduce) { .document-card:hover { transform: none; } }
</style>
