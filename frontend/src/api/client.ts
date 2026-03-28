/**
 * LocalLens Core API Client
 * Orchestrates communication between the frontend and the local RAG engine.
 */

import axios from 'axios';
import type { Document, QueryResult, IngestionStatus, ChatSession, ChatMessage } from '../types';

const api = axios.create({
  baseURL: '/api',
});

/**
 * Retrieval & Ingestion
 */

export const getDocuments = async (): Promise<Document[]> => {
  try {
    const response = await api.get<Document[]>('/documents');
    return response.data;
  } catch (error) {
    console.error('Error fetching documents:', error);
    return [];
  }
};

export const ingestFiles = async (files: File[]): Promise<{ job_id: string } | null> => {
  try {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const response = await api.post<{ job_id: string }>('/ingest', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  } catch (error) {
    console.error('Error ingesting files:', error);
    return null;
  }
};

export const getIngestionStatus = async (jobId: string): Promise<IngestionStatus | null> => {
  try {
    const response = await api.get<IngestionStatus>(`/ingest/status/${jobId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching ingestion status:', error);
    return null;
  }
};

/**
 * Search & Query
 */

export const queryDocs = async (query: string, session_id?: string): Promise<QueryResult | null> => {
  try {
    const response = await api.post<QueryResult>('/query', { query, session_id });
    return response.data;
  } catch (error) {
    console.error('Error querying documents:', error);
    return null;
  }
};

export const queryDocsStream = async (
  query: string, 
  session_id: string | undefined, 
  onUpdate: (data: Partial<QueryResult> & { done: boolean }) => void
): Promise<void> => {
  const response = await fetch('/api/query/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id }),
  });

  if (!response.ok) {
    let detail = '';
    try {
      detail = await response.text();
    } catch {
      detail = '';
    }
    const suffix = detail ? `: ${detail}` : '';
    throw new Error(`Streaming query failed (${response.status})${suffix}`);
  }

  if (!response.body) {
    throw new Error('Streaming query failed: empty response body');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let receivedDone = false;

  while (true) {
    const { value, done } = await reader.read();

    if (value) {
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data?.done) receivedDone = true;
          onUpdate(data);
        } catch {
          // Ignore malformed SSE chunks and continue processing.
        }
      }
    }

    if (done) break;
  }

  if (!receivedDone) {
    throw new Error('Streaming query terminated before completion');
  }
};

export const searchByImage = async (file: File, sessionId?: string): Promise<QueryResult | null> => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) formData.append('session_id', sessionId);
    
    const response = await api.post<QueryResult>('/search/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  } catch (error) {
    console.error('Error in image search:', error);
    return null;
  }
};

/**
 * Session Management
 */

export const getSessions = async (): Promise<ChatSession[]> => {
  try {
    const response = await api.get<ChatSession[]>('/sessions');
    return response.data;
  } catch (error) {
    console.error('Error fetching sessions:', error);
    return [];
  }
};

export const createSession = async (title?: string): Promise<{ session_id: string } | null> => {
  try {
    const response = await api.post<{ session_id: string }>('/sessions', null, {
      params: { title },
    });
    return response.data;
  } catch (error) {
    console.error('Error creating session:', error);
    return null;
  }
};

export const deleteSession = async (sessionId: string): Promise<boolean> => {
  try {
    await api.delete(`/sessions/${sessionId}`);
    return true;
  } catch (error) {
    console.error('Error deleting session:', error);
    return false;
  }
};

export const getSessionMessages = async (sessionId: string): Promise<ChatMessage[]> => {
  try {
    const response = await api.get<ChatMessage[]>(`/sessions/${sessionId}/messages`);
    return response.data;
  } catch (error) {
    console.error('Error fetching session messages:', error);
    return [];
  }
};

/**
 * Document Context Control
 */

export const deleteDocument = async (docId: string): Promise<boolean> => {
  try {
    await api.delete(`/documents/${docId}`);
    return true;
  } catch (error) {
    console.error('Error deleting document:', error);
    return false;
  }
};

export const getDocumentDetails = async (docId: string): Promise<any> => {
  try {
    const response = await api.get(`/documents/${docId}/details`);
    return response.data;
  } catch (error) {
    console.error('Error fetching document details:', error);
    return null;
  }
};

export const getSessionDocs = async (sessionId: string): Promise<string[]> => {
  try {
    const response = await api.get<{ doc_ids: string[] }>(`/sessions/${sessionId}/documents`);
    return response.data.doc_ids;
  } catch (error) {
    console.error('Error fetching session docs:', error);
    return [];
  }
};

export const addDocToSession = async (sessionId: string, docId: string): Promise<boolean> => {
  try {
    await api.post(`/sessions/${sessionId}/documents/${docId}`);
    return true;
  } catch (error) {
    console.error('Error adding doc to session:', error);
    return false;
  }
};

export const addDocsToSessionBulk = async (sessionId: string, docIds: string[]): Promise<boolean> => {
  try {
    await api.post(`/sessions/${sessionId}/documents/bulk/add`, docIds);
    return true;
  } catch (error) {
    console.error('Error adding docs bulk:', error);
    return false;
  }
};

export const removeDocFromSession = async (sessionId: string, docId: string): Promise<boolean> => {
  try {
    await api.delete(`/sessions/${sessionId}/documents/${docId}`);
    return true;
  } catch (error) {
    console.error('Error removing doc from session:', error);
    return false;
  }
};

export const removeDocsFromSessionBulk = async (sessionId: string, docIds: string[]): Promise<boolean> => {
  try {
    await api.post(`/sessions/${sessionId}/documents/bulk/remove`, docIds);
    return true;
  } catch (error) {
    console.error('Error removing docs bulk:', error);
    return false;
  }
};

export const clearSessionDocs = async (sessionId: string): Promise<boolean> => {
  try {
    await api.delete(`/sessions/${sessionId}/documents/bulk/clear`);
    return true;
  } catch (error) {
    console.error('Error clearing session docs:', error);
    return false;
  }
};

export default api;
