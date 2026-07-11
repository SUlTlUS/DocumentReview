<script setup lang="ts">
import MarkdownIt from 'markdown-it'
import { nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getChatHistory, getDocument, getErrorMessage, sendMessage } from '../api'
import KineticTitle from '../components/KineticTitle.vue'
import type { ChatMessage, DocumentRecord } from '../types/api'

const route = useRoute(); const documentId = Number(route.params.id)
const document = ref<DocumentRecord | null>(null); const messages = ref<ChatMessage[]>([]); const sessionId = ref<number | null>(null)
const question = ref(''); const loading = ref(false); const initialLoading = ref(true); const error = ref(''); const conversation = ref<HTMLElement | null>(null)
const suggestions = ['违约责任怎么约定的？', '合同缺少哪些保护性条款？', '验收标准是否清晰？', '双方权利义务是否对等？']
const markdown = new MarkdownIt({ html: false, linkify: true, breaks: true })
const render = (content: string) => markdown.render(content)
async function scrollToBottom() { await nextTick(); conversation.value?.scrollTo({ top: conversation.value.scrollHeight, behavior: 'smooth' }) }
async function submit(value = question.value) {
  const trimmed = value.trim(); if (!trimmed || loading.value) return
  question.value = ''; error.value = ''; loading.value = true
  const now = new Date().toISOString(); messages.value.push({ id: -Date.now(), role: 'user', content: trimmed, created_at: now }); await scrollToBottom()
  try { const response = await sendMessage(documentId, trimmed, sessionId.value); sessionId.value = response.session_id; messages.value.push({ id: -(Date.now() + 1), role: 'assistant', content: response.answer, created_at: new Date().toISOString() }); await scrollToBottom() } catch (reason) { error.value = getErrorMessage(reason) } finally { loading.value = false }
}
onMounted(async () => { try { document.value = await getDocument(documentId); const history = await getChatHistory(documentId); messages.value = history.messages; sessionId.value = history.session_id; await scrollToBottom() } catch (reason) { error.value = getErrorMessage(reason) } finally { initialLoading.value = false } })
</script>

<template>
  <section class="page-container chat-page">
    <KineticTitle eyebrow="Q & A / Evidence" title="文档问答" :description="document ? `${document.filename} · 回答将引用检索到的原文` : '通过引用原文的回答定位关键条款。'" />
    <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
    <div class="chat-shell panel">
      <div ref="conversation" class="conversation" aria-live="polite">
        <div v-if="initialLoading" class="chat-loading skeleton"></div>
        <div v-else-if="messages.length === 0" class="chat-empty"><span>ASK WITH EVIDENCE</span><h2>从一个关键问题开始</h2><p>系统会检索最相关的五个文本块，并在回答中引用依据。</p><div class="suggestions"><button v-for="suggestion in suggestions" :key="suggestion" type="button" @click="submit(suggestion)">{{ suggestion }}</button></div></div>
        <article v-for="message in messages" :key="message.id" class="message" :class="message.role"><span>{{ message.role === 'user' ? 'YOU' : 'RAG ASSISTANT' }}</span><div v-if="message.role === 'assistant'" class="markdown" v-html="render(message.content)"></div><p v-else>{{ message.content }}</p></article>
        <div v-if="loading" class="typing" aria-label="AI 正在生成回答"><span>READ</span><span>THINK</span><span>CITE</span></div>
      </div>
      <form class="composer" @submit.prevent="submit()"><label for="question">针对当前文档提问</label><div><textarea id="question" v-model.trim="question" rows="2" maxlength="2000" placeholder="例如：违约责任是否对双方同等适用？" @keydown.ctrl.enter.prevent="submit()"></textarea><button class="button button-primary" type="submit" :disabled="loading || !question.trim()">{{ loading ? '回答中' : '发送' }}</button></div><small>Ctrl + Enter 发送 · 最近四轮对话会作为上下文</small></form>
    </div>
  </section>
</template>

<style scoped>
.chat-shell { display: grid; grid-template-rows: minmax(420px, 58vh) auto; overflow: hidden; margin-top: 36px; }.conversation { overflow-y: auto; padding: 24px; scroll-behavior: smooth; }.chat-loading { height: 100%; border-radius: 12px; }.chat-empty { display: grid; min-height: 100%; place-content: center; text-align: center; }.chat-empty > span { color: var(--accent); font-family: "Cascadia Code", monospace; font-size: 11px; letter-spacing: .16em; }.chat-empty h2 { margin-bottom: 8px; }.chat-empty p { max-width: 520px; margin: 0 auto; color: var(--muted); }.suggestions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 28px; }.suggestions button { border: 1px solid var(--border); border-radius: 10px; background: var(--bg); padding: 12px; color: var(--text); cursor: pointer; text-align: left; transition: border-color 160ms ease-out, background 160ms ease-out; }.suggestions button:hover { border-color: var(--accent); background: rgba(88, 166, 255, .07); }.message { max-width: 78%; margin-bottom: 18px; border: 1px solid var(--border); border-radius: 14px; padding: 14px 16px; animation: message-enter 220ms ease-out both; }.message > span { display: block; margin-bottom: 7px; color: var(--muted); font-family: "Cascadia Code", monospace; font-size: 9px; letter-spacing: .13em; }.message p { margin: 0; white-space: pre-wrap; line-height: 1.65; }.message.user { margin-left: auto; border-color: rgba(88, 166, 255, .55); background: var(--accent-strong); }.message.user > span { color: rgba(255, 255, 255, .72); }.message.assistant { background: var(--surface-strong); }.markdown :deep(p) { margin: 0 0 10px; line-height: 1.65; }.markdown :deep(p:last-child) { margin-bottom: 0; }.markdown :deep(blockquote) { margin: 10px 0; border-left: 3px solid var(--accent); padding-left: 12px; color: var(--muted); }.typing { display: flex; gap: 12px; color: var(--accent); font-family: "Cascadia Code", monospace; font-size: 10px; letter-spacing: .12em; }.typing span { animation: typing-word 1.2s ease-in-out infinite; }.typing span:nth-child(2) { animation-delay: 160ms; }.typing span:nth-child(3) { animation-delay: 320ms; }@keyframes typing-word { 0%, 70%, 100% { opacity: .28; transform: translateY(0); } 35% { opacity: 1; transform: translateY(-3px); } }@keyframes message-enter { from { opacity: 0; transform: translateY(8px); } }.composer { border-top: 1px solid var(--border); background: rgba(13, 17, 23, .88); padding: 18px; }.composer label { display: block; margin-bottom: 8px; color: var(--muted); font-size: 12px; font-weight: 700; }.composer > div { display: flex; align-items: end; gap: 10px; }.composer textarea { width: 100%; min-height: 64px; resize: vertical; border: 1px solid var(--border); border-radius: 10px; background: var(--bg); padding: 12px 14px; color: var(--text); line-height: 1.5; }.composer textarea:focus { border-color: var(--accent); }.composer small { display: block; margin-top: 8px; color: var(--muted); }
@media (max-width: 640px) { .chat-shell { grid-template-rows: minmax(420px, 60vh) auto; }.conversation { padding: 16px; }.suggestions { grid-template-columns: 1fr; }.message { max-width: 92%; }.composer > div { align-items: stretch; flex-direction: column; } }
@media (prefers-reduced-motion: reduce) { .conversation { scroll-behavior: auto; }.message, .typing span { animation: none; } }
</style>
