export interface Document {
  doc_id: string
  filename: string
  page_count: number
  chunk_count: number
  ingested_at: string
}

export interface CitationCard {
  doc_name: string
  page_number: number
  chunk_text: string
  char_start: number
  char_end: number
  source_type: 'text' | 'image'
  bbox: [number, number, number, number] | null
  verified: boolean
}

export interface QueryResult {
  answer: string
  verified: boolean
  flagged_sentences: string[]
  citations: CitationCard[]
  latency_seconds: number
}

export interface IngestionStatus {
  filename: string
  current_page: number
  total_pages: number
  stage: 'extracting' | 'ocr' | 'embedding' | 'indexing' | 'done' | 'error'
  log_lines: string[]
}

export interface ChatSession {
  session_id: string
  title: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  message_id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  citations?: CitationCard[]
  created_at: string
}
