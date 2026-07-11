export type DocumentStatus = 'uploaded' | 'parsing' | 'ready' | 'parse_failed'
export type ReviewStatus = 'pending' | 'reviewing' | 'completed' | 'review_failed'
export type Severity = 'high' | 'medium' | 'low'

export interface HealthStatus { status: string; llm_provider: string; deepseek_api_configured: boolean; version: string }

export interface DocumentRecord {
  id: number; filename: string; file_type: string; file_size: number; status: DocumentStatus;
  review_status: ReviewStatus; upload_time: string; content_summary: string; chunk_count: number;
  parse_method: string; last_error: string | null
}
export interface DocumentUploadResponse { document: DocumentRecord; message: string; chunk_count: number }
export interface DocumentListResponse { items: DocumentRecord[]; total: number }
export interface ReviewItem { id: number; category: string; severity: Severity; title: string; description: string; suggestion: string; source_text: string }
export interface ReviewResult { id: number; document_id: number; review_time: string; status: string; total_items: number; risk_count: number; summary: string; duration_ms: number; pipeline_version: string; prompt_version: string; error_message: string | null; items: ReviewItem[] }
export interface ChatMessage { id: number; role: 'user' | 'assistant'; content: string; created_at: string }
export interface ChatHistory { session_id: number | null; messages: ChatMessage[] }
export interface ChatResponse { answer: string; session_id: number }
