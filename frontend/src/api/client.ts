import axios from 'axios';
import type { Document, QueryResult, IngestionStatus } from '../types';

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

export const queryDocs = async (query: string): Promise<QueryResult | null> => {
  try {
    const response = await api.post<QueryResult>('/query', { query });
    return response.data;
  } catch (error) {
    console.error('Error querying documents:', error);
    return null;
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

export default api;
