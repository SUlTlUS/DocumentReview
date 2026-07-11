import axios from 'axios'
import type { ChatHistory, ChatResponse, DocumentListResponse, DocumentRecord, DocumentUploadResponse, ReviewResult } from '../types/api'

const api = axios.create({ baseURL: '', timeout: 65_000, headers: { Accept: 'application/json' } })

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> { const form = new FormData(); form.append('file', file); return (await api.post('/api/documents/upload', form)).data }
export async function getDocuments(): Promise<DocumentListResponse> { return (await api.get('/api/documents')).data }
export async function getDocument(id: number): Promise<DocumentRecord> { return (await api.get(`/api/documents/${id}`)).data }
export async function deleteDocument(id: number): Promise<void> { await api.delete(`/api/documents/${id}`) }
export async function triggerReview(id: number): Promise<ReviewResult> { return (await api.post(`/api/documents/${id}/review`)).data }
export async function getReviewResult(id: number): Promise<ReviewResult> { return (await api.get(`/api/documents/${id}/review`)).data }
export async function sendMessage(id: number, question: string, sessionId?: number | null): Promise<ChatResponse> { return (await api.post(`/api/documents/${id}/chat`, { question, session_id: sessionId ?? null })).data }
export async function getChatHistory(id: number, sessionId?: number | null): Promise<ChatHistory> { return (await api.get(`/api/documents/${id}/chat/history`, { params: sessionId ? { session_id: sessionId } : {} })).data }
export function getErrorMessage(error: unknown): string { if (axios.isAxiosError(error)) return String(error.response?.data?.detail ?? error.response?.data?.message ?? error.message); return error instanceof Error ? error.message : '发生未知错误' }
export function isNotFound(error: unknown): boolean { return axios.isAxiosError(error) && error.response?.status === 404 }
