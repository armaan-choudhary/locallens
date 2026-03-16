import axios from 'axios';
import type { Document, QueryResult, IngestionStatus, ChatSession, ChatMessage } from '../types';

const api = axios.create({
  baseURL: '/api',
});

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

export const queryDocs = async (query: string, session_id?: string): Promise<QueryResult | null> => {
  try {
    const response = await api.post<QueryResult>('/query', { query, session_id });
    return response.data;
  } catch (error) {
    console.error('Error querying documents:', error);
    return null;
  }
};

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

export const deleteDocument = async (docId: string): Promise<boolean> => {
  try {
    await api.delete(`/documents/${docId}`);
    return true;
  } catch (error) {
    console.error('Error deleting document:', error);
    return false;
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

export const removeDocFromSession = async (sessionId: string, docId: string): Promise<boolean> => {
  try {
    await api.delete(`/sessions/${sessionId}/documents/${docId}`);
    return true;
  } catch (error) {
    console.error('Error removing doc from session:', error);
    return false;
  }
};

export default api;
