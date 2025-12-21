export interface StructureNoteResponse {
    structured_content: string;
}

export async function structureNote(noteId: string, content: string): Promise<StructureNoteResponse> {
    const response = await fetch('/api/notes/structure', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            note_id: noteId,
            content: content
        }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to structure note: ${response.status} ${errorText}`);
    }

    return response.json();
}

export interface ChatResponse {
    reply: string;
    updated_note_content?: string | null;
}

export async function chatWithAI(message: string, currentNoteContent?: string, noteId?: string, fileUri?: string): Promise<ChatResponse> {
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message,
            current_note_content: currentNoteContent,
            noteId,
            file_uri: fileUri
        }),
    });

    if (!response.ok) {
        throw new Error(`Failed to chat with AI: ${response.status}`);
    }

    return response.json();
}

export interface UploadResponse {
    id: string;
    name: string;
    file_uri: string;
    type: string;
}

export async function uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        throw new Error(`Failed to upload file: ${response.status}`);
    }

    return response.json();
}
