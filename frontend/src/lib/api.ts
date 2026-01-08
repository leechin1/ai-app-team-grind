/**
 * API Client for AI Study App Backend
 *
 * Connects to FastAPI backend at http://localhost:8000
 */

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ==================== Types ====================

export interface FlashCard {
  id: string;
  front: string;
  back: string;
  difficulty: 'easy' | 'medium' | 'hard';
  tags: string[];
  interval: number;
  repetitions: number;
  ease_factor: number;
  last_reviewed_at?: string;
  next_review_date?: string;
  review_count: number;
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correct_answer_index: number;
  explanation: string;
  concept: string;
}

export interface MatchPair {
  id: string;
  prompt: string;
  answer: string;
  hint?: string;
  tags: string[];
}

export interface GenerateFlashcardsRequest {
  content: string;
  num_flashcards?: number;
  difficulty?: 'easy' | 'medium' | 'hard';
  focus_topics?: string[];
}

export interface GenerateQuizRequest {
  content: string;
  num_questions?: number;
  difficulty?: 'easy' | 'medium' | 'hard';
  focus_topics?: string[];
}

export interface GenerateMatchQuizRequest {
  content: string;
  num_pairs?: number;
  difficulty?: 'easy' | 'medium' | 'hard';
  focus_topics?: string[];
}

export interface ReviewFlashcardRequest {
  flashcard_id: string;
  response_quality: number; // 0-5
  was_correct: boolean;
  time_spent_seconds: number;
}

export interface Stats {
  total_interactions: number;
  verified_interactions: number;
  self_reported_interactions: number;
  overall_accuracy: number;
  flashcards: {
    total: number;
    due: number;
  };
  by_type: {
    flashcard_review: number;
    quiz_attempt: number;
    match_attempt: number;
  };
}

// ==================== Project Types ====================

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  icon?: string;
  color?: string;
}

// ==================== Helper Functions ====================

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error (${response.status}): ${errorText}`);
  }

  return response.json();
}

// ==================== Project API ====================

export const projectAPI = {
  /**
   * Get all projects for the current user
   */
  async list() {
    const response = await fetchAPI<{ projects: Project[] }>('/api/projects', {
      method: 'GET',
    });
    return response.projects;
  },

  /**
   * Get a specific project by ID
   */
  async getById(project_id: string) {
    return fetchAPI<Project>(`/api/projects/${project_id}`, {
      method: 'GET',
    });
  },

  /**
   * Create a new project
   */
  async create(request: CreateProjectRequest) {
    return fetchAPI<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Update a project
   */
  async update(project_id: string, request: Partial<CreateProjectRequest>) {
    return fetchAPI<Project>(`/api/projects/${project_id}`, {
      method: 'PUT',
      body: JSON.stringify(request),
    });
  },

  /**
   * Delete a project
   */
  async delete(project_id: string) {
    return fetchAPI<{ message: string }>(`/api/projects/${project_id}`, {
      method: 'DELETE',
    });
  },
};

// ==================== Flashcard API ====================

export const flashcardAPI = {
  /**
   * Generate flashcards from text content
   */
  async generate(request: GenerateFlashcardsRequest) {
    // Map frontend field names to backend expected names
    const backendRequest = {
      content: request.content,
      num_cards: request.num_flashcards || 10,
      difficulty_filter: request.difficulty,
    };
    
    return fetchAPI<{ flashcards: FlashCard[] }>('/api/flashcards/generate', {
      method: 'POST',
      body: JSON.stringify(backendRequest),
    });
  },

  /**
   * Get flashcards that are due for review
   */
  async getDue() {
    return fetchAPI<{ due_cards: FlashCard[]; total_due: number }>('/api/flashcards/due', {
      method: 'GET',
    });
  },

  /**
   * Get a specific flashcard by ID
   */
  async getById(flashcard_id: string) {
    return fetchAPI<FlashCard>(`/api/flashcards/${flashcard_id}`, {
      method: 'GET',
    });
  },

  /**
   * Submit a flashcard review (SM-2 spaced repetition)
   */
  async review(request: ReviewFlashcardRequest) {
    return fetchAPI<{
      flashcard: FlashCard;
      stats: any;
      message: string
    }>('/api/flashcards/review', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Get flashcards by document (filtered or grouped)
   */
  async byDocument(documentId?: string) {
    const url = documentId
      ? `/api/flashcards/by-document?document_id=${documentId}`
      : '/api/flashcards/by-document';

    return fetchAPI<{
      by_document?: Array<{
        document_id: string;
        document_name: string;
        flashcards: FlashCard[];
        count: number;
      }>;
      flashcards?: FlashCard[];
      total: number;
      document_id?: string;
    }>(url);
  },
};

// ==================== Quiz API ====================

export const quizAPI = {
  /**
   * Generate a multiple-choice quiz
   */
  async generate(request: GenerateQuizRequest) {
    return fetchAPI<{ quiz_id: string; questions: QuizQuestion[] }>('/api/quiz/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Submit quiz answers
   */
  async submit(quiz_id: string, answers: any[]) {
    return fetchAPI<{ quiz_id: string; message: string }>('/api/quiz/submit', {
      method: 'POST',
      body: JSON.stringify({ quiz_id, answers }),
    });
  },
};

// ==================== Match Quiz API ====================

export const matchAPI = {
  /**
   * Generate a matching quiz
   */
  async generate(request: GenerateMatchQuizRequest) {
    return fetchAPI<{ match_quiz_id: string; pairs: MatchPair[] }>('/api/match/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Submit match quiz answers
   */
  async submit(match_quiz_id: string, answers: any[]) {
    return fetchAPI<{ match_quiz_id: string; message: string }>('/api/match/submit', {
      method: 'POST',
      body: JSON.stringify({ match_quiz_id, answers }),
    });
  },
};

// ==================== Stats & Analytics API ====================

export const statsAPI = {
  /**
   * Get overall statistics
   */
  async getStats() {
    return fetchAPI<Stats>('/api/stats', {
      method: 'GET',
    });
  },

  /**
   * Check ML training readiness
   */
  async checkMLReadiness() {
    return fetchAPI<{
      ready: boolean;
      requirements: Record<string, boolean>;
      current_stats: Stats;
      ml_confidence: number;
    }>('/api/stats/ml-readiness', {
      method: 'GET',
    });
  },
};

// ==================== Document Upload API ====================

export const documentAPI = {
  /**
   * Upload a document (PDF, TXT, etc.)
   */
  async upload(file: File, projectId: string) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/documents/upload?project_id=${projectId}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to upload document: ${response.status}`);
    }

    return response.json() as Promise<{
      id: string;
      filename: string;
      content: string;
      preview: string;
      metadata: any;
    }>;
  },

  /**
   * List all uploaded documents for a project
   */
  async list(projectId: string) {
    return fetchAPI<{ documents: Array<{
      id: string;
      filename: string;
      preview: string;
      uploaded_at: string;
    }>; total: number }>(`/api/projects/${projectId}/documents`);
  },

  /**
   * Get a specific document by ID
   */
  async getById(doc_id: string) {
    return fetchAPI<{
      id: string;
      filename: string;
      content: string;
      preview: string;
      uploaded_at: string;
      metadata: any;
    }>(`/api/documents/${doc_id}`);
  },
};

// ==================== Helper Functions for Dashboard ====================

/**
 * Upload a file (wrapper for documentAPI.upload with transformed response)
 */
export async function uploadFile(file: File) {
  const result = await documentAPI.upload(file);
  return {
    id: Date.now().toString(),
    name: result.filename,
    file_uri: `data/uploads/${result.filename}`,
    content: result.content,
    preview: result.preview,
    metadata: result.metadata,
  };
}

/**
 * Structure a note using AI
 */
export async function structureNote(noteId: string, content: string) {
  return fetchAPI<{
    note_id: string;
    structured_content: string;
    message: string;
  }>('/api/notes/structure', {
    method: 'POST',
    body: JSON.stringify({
      note_id: noteId,
      content: content,
    }),
  });
}

/**
 * Chat with AI about a document or note
 */
export async function chatWithAI(
  message: string,
  context?: string,
  sourceId?: string,
  fileUri?: string
) {
  return fetchAPI<{
    reply: string;
    updated_note_content?: string;
    message: string;
  }>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      message: message,
      context: context,
      source_id: sourceId,
      file_uri: fileUri,
    }),
  });
}

// ==================== Health Check API ====================

export const healthAPI = {
  /**
   * Check API health status
   */
  async check() {
    return fetchAPI<{
      status: string;
      api_key_configured: boolean;
      flashcards_count: number;
      interactions_logged: number;
    }>('/health', {
      method: 'GET',
    });
  },
};

// Export default API object
export default {
  project: projectAPI,
  flashcard: flashcardAPI,
  quiz: quizAPI,
  match: matchAPI,
  stats: statsAPI,
  document: documentAPI,
  health: healthAPI,
};
