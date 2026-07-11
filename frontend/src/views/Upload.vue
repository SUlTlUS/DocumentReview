<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getErrorMessage, uploadDocument } from '../api'
import KineticTitle from '../components/KineticTitle.vue'
import type { DocumentUploadResponse } from '../types/api'

const input = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const uploading = ref(false)
const error = ref('')
const result = ref<DocumentUploadResponse | null>(null)
const accepted = new Set(['pdf', 'docx', 'txt'])

function selectFile() { input.value?.click() }
function validate(file: File): string | null {
  const extension = file.name.split('.').pop()?.toLowerCase() ?? ''
  if (!accepted.has(extension)) return '仅支持 PDF、DOCX、TXT 格式。'
  if (file.size === 0) return '不能上传空文件。'
  if (file.size > 10 * 1024 * 1024) return '文件不能超过 10MB。'
  return null
}
async function handleFile(file?: File) {
  if (!file || uploading.value) return
  error.value = validate(file) ?? ''
  if (error.value) return
  uploading.value = true; result.value = null
  try { result.value = await uploadDocument(file) } catch (reason) { error.value = getErrorMessage(reason) } finally { uploading.value = false }
}
function onDrop(event: DragEvent) { dragging.value = false; void handleFile(event.dataTransfer?.files[0]) }
</script>

<template>
  <section class="page-container">
    <KineticTitle eyebrow="Intake / 02" title="上传文档" description="拖入合同，系统将提取正文、建立索引并准备审核。支持 PDF、DOCX 和 TXT，单文件不超过 10MB。" />
    <div
      class="upload-zone panel"
      :class="{ 'is-dragging': dragging, 'is-uploading': uploading }"
      role="button" tabindex="0" :aria-busy="uploading"
      @click="selectFile" @keydown.enter="selectFile" @keydown.space.prevent="selectFile"
      @dragenter.prevent="dragging = true" @dragover.prevent="dragging = true" @dragleave.prevent="dragging = false" @drop.prevent="onDrop"
    >
      <input ref="input" class="visually-hidden" type="file" accept=".pdf,.docx,.txt" @change="handleFile(($event.target as HTMLInputElement).files?.[0])" />
      <div class="upload-glyph" aria-hidden="true"><span></span><span></span><span></span></div>
      <strong>{{ uploading ? '正在解析与建立索引' : '拖拽文件到此处' }}</strong>
      <p>{{ uploading ? '请保持页面打开，完成后会显示索引数量。' : '或点击选择本地文件' }}</p>
      <div v-if="uploading" class="loading-words" aria-hidden="true"><span>READ</span><span>PARSE</span><span>INDEX</span></div>
    </div>
    <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
    <article v-if="result" class="result-card panel" aria-live="polite">
      <div><span class="result-label">UPLOAD COMPLETE</span><h2>{{ result.document.filename }}</h2><p>{{ result.message }}</p></div>
      <div class="chunk-metric"><strong>{{ result.chunk_count }}</strong><span>TEXT CHUNKS</span></div>
      <div class="result-actions">
        <RouterLink class="button button-primary" :to="`/documents/${result.document.id}/review`">去审核</RouterLink>
        <RouterLink class="button" :to="`/documents/${result.document.id}/chat`">去问答</RouterLink>
      </div>
    </article>
  </section>
</template>

<style scoped>
.upload-zone { display: grid; min-height: 340px; place-items: center; gap: 12px; margin-top: 38px; border-style: dashed; padding: 40px; text-align: center; cursor: pointer; transition: border-color 180ms ease-out, background 180ms ease-out, transform 180ms ease-out; }
.upload-zone:hover, .upload-zone.is-dragging { border-color: var(--accent); background: rgba(88, 166, 255, 0.07); transform: translateY(-2px); }
.upload-zone strong { font-size: 20px; }
.upload-zone p { margin: 0; color: var(--muted); }
.upload-glyph { position: relative; width: 74px; height: 74px; border: 1px solid rgba(88, 166, 255, 0.38); border-radius: 20px; background: rgba(88, 166, 255, 0.08); }
.upload-glyph span { position: absolute; left: 50%; width: 28px; height: 2px; background: var(--accent); transform: translateX(-50%); }
.upload-glyph span:nth-child(1) { top: 25px; width: 2px; height: 24px; }
.upload-glyph span:nth-child(2) { top: 25px; transform: translateX(-50%) rotate(45deg); transform-origin: right; width: 12px; }
.upload-glyph span:nth-child(3) { top: 25px; transform: translateX(-50%) rotate(-45deg); transform-origin: left; width: 12px; }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.loading-words { display: flex; gap: 16px; margin-top: 12px; color: var(--accent); font-family: "Cascadia Code", monospace; font-size: 11px; letter-spacing: 0.12em; }
.loading-words span { animation: word-pulse 1.2s ease-in-out infinite; }
.loading-words span:nth-child(2) { animation-delay: 160ms; }.loading-words span:nth-child(3) { animation-delay: 320ms; }
@keyframes word-pulse { 0%, 70%, 100% { opacity: .32; transform: translateY(0); } 35% { opacity: 1; transform: translateY(-3px); } }
.result-card { display: grid; grid-template-columns: 1fr auto; gap: 20px; margin-top: 24px; padding: 24px; }
.result-card h2 { margin: 6px 0; font-size: 20px; }.result-card p { margin: 0; color: var(--muted); }
.result-label { color: var(--success); font-family: "Cascadia Code", monospace; font-size: 11px; letter-spacing: .14em; }
.chunk-metric { display: grid; align-content: center; text-align: right; }.chunk-metric strong { color: var(--accent); font-size: 42px; line-height: 1; }.chunk-metric span { margin-top: 6px; color: var(--muted); font-size: 10px; letter-spacing: .1em; }
.result-actions { display: flex; grid-column: 1 / -1; gap: 10px; }
@media (max-width: 640px) { .upload-zone { min-height: 290px; padding: 28px 18px; }.result-card { grid-template-columns: 1fr; }.chunk-metric { text-align: left; }.result-actions { flex-wrap: wrap; } }
@media (prefers-reduced-motion: reduce) { .upload-zone:hover { transform: none; }.loading-words span { animation: none; opacity: 1; } }
</style>
