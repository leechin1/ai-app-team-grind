import { useState, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { FileText, Upload as UploadIcon, File, Check, Brain, Target, Zap, Trash2, Edit } from "lucide-react";
import ProjectLayout from "@/components/ProjectLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { documentAPI, noteAPI } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function Upload() {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [lastUploadedDoc, setLastUploadedDoc] = useState<any>(null);

  // Fetch list of uploaded documents
  const { data: documentsData } = useQuery({
    queryKey: ['documents', projectId],
    queryFn: () => {
      if (!projectId) throw new Error("No project selected");
      return documentAPI.list(projectId);
    },
    enabled: !!projectId,
  });

  // Fetch list of notes
  const { data: notesData } = useQuery({
    queryKey: ['notes', projectId],
    queryFn: () => {
      if (!projectId) throw new Error("No project selected");
      return noteAPI.list(projectId);
    },
    enabled: !!projectId,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      if (!projectId) {
        throw new Error("No project selected");
      }
      return documentAPI.upload(file, projectId);
    },
    onSuccess: (data) => {
      setLastUploadedDoc(data);
      setShowSuccessDialog(true);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success(`File "${data.filename}" uploaded successfully!`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to upload file: ${error.message}`);
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Reset input so same file can be selected again
    event.target.value = '';

    uploadMutation.mutate(file);
  };

  const handleUseDocument = (destination: 'flashcards' | 'quiz' | 'match') => {
    if (!lastUploadedDoc || !projectId) return;

    setShowSuccessDialog(false);

    // Navigate to the destination with the content
    navigate(`/project/${projectId}/${destination}`, { state: {
      content: lastUploadedDoc.content,
      documentId: lastUploadedDoc.id,
      documentName: lastUploadedDoc.filename
    } });
  };

  const handleUseExistingDocument = async (doc: any, destination: 'flashcards' | 'quiz' | 'match') => {
    if (!projectId) return;

    // Fetch full document content first (list only has preview)
    try {
      const fullDoc = await documentAPI.getById(doc.id);
      navigate(`/project/${projectId}/${destination}`, { state: {
        content: fullDoc.content,
        documentId: fullDoc.id,
        documentName: fullDoc.filename
      } });
    } catch (error) {
      toast.error('Failed to load document content');
      console.error('Error loading document:', error);
    }
  };

  const handleUseNote = (note: any, destination: 'flashcards' | 'quiz' | 'match') => {
    if (!projectId) return;

    // Strip HTML tags from content_html to get plain text
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = note.content_html || note.content || '';
    const plainText = tempDiv.textContent || tempDiv.innerText || '';

    navigate(`/project/${projectId}/${destination}`, { state: {
      content: plainText,
      documentId: note.id,
      documentName: note.title
    } });
  };

  return (
    <ProjectLayout>
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Upload Study Material</h1>
            <p className="text-muted-foreground">
              Upload PDF or text files to generate flashcards, quizzes, or match games
            </p>
          </div>

          {/* Upload Card */}
          <Card>
            <CardContent className="pt-6">
              <div
                className={`border-2 border-dashed border-border rounded-lg p-12 text-center cursor-pointer transition-colors ${
                  uploadMutation.isPending ? 'opacity-50' : 'hover:border-primary/50'
                }`}
                onClick={() => !uploadMutation.isPending && fileInputRef.current?.click()}
              >
                <UploadIcon className={`w-12 h-12 mx-auto mb-4 text-muted-foreground ${
                  uploadMutation.isPending ? 'animate-bounce' : ''
                }`} />
                <h3 className="text-lg font-semibold mb-2">
                  {uploadMutation.isPending ? 'Uploading and processing...' : 'Click to upload'}
                </h3>
                <p className="text-sm text-muted-foreground">
                  PDF, TXT files supported
                </p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt"
                onChange={handleFileSelect}
                className="hidden"
                disabled={uploadMutation.isPending}
              />
            </CardContent>
          </Card>

          {/* Uploaded Documents */}
          {documentsData && documentsData.documents.length > 0 && (
            <div>
              <h2 className="text-xl font-bold mb-4">Your Uploaded Documents</h2>
              <div className="grid grid-cols-1 gap-4">
                {documentsData.documents.map((doc) => (
                  <Card key={doc.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                            <File className="w-6 h-6 text-primary" />
                          </div>
                          <div>
                            <CardTitle className="text-lg">{doc.filename}</CardTitle>
                            <CardDescription>
                              Uploaded {new Date(doc.uploaded_at).toLocaleDateString()}
                            </CardDescription>
                          </div>
                        </div>
                        <Badge variant="outline" className="bg-green-500/20">
                          <Check className="w-3 h-3 mr-1" />
                          Ready
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                        {doc.preview}
                      </p>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleUseExistingDocument(doc, 'flashcards')}
                        >
                          <Brain className="w-4 h-4 mr-2" />
                          Flashcards
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleUseExistingDocument(doc, 'quiz')}
                        >
                          <Target className="w-4 h-4 mr-2" />
                          Quiz
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleUseExistingDocument(doc, 'match')}
                        >
                          <Zap className="w-4 h-4 mr-2" />
                          Match
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          {notesData && notesData.notes.length > 0 && (
            <div>
              <h2 className="text-xl font-bold mb-4">Your Notes</h2>
              <div className="grid grid-cols-1 gap-4">
                {notesData.notes.map((note) => (
                  <Card key={note.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
                            <FileText className="w-6 h-6 text-blue-500" />
                          </div>
                          <div>
                            <CardTitle className="text-lg">{note.title}</CardTitle>
                            <CardDescription>
                              Last modified {new Date(note.updated_at).toLocaleDateString()}
                            </CardDescription>
                          </div>
                        </div>
                        <Badge variant="outline" className="bg-blue-500/20">
                          {note.type}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigate(`/project/${projectId}/editor/${note.id}`)}
                        >
                          <Edit className="w-4 h-4 mr-2" />
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleUseNote(note, 'flashcards')}
                        >
                          <Brain className="w-4 h-4 mr-2" />
                          Flashcards
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleUseNote(note, 'quiz')}
                        >
                          <Target className="w-4 h-4 mr-2" />
                          Quiz
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleUseNote(note, 'match')}
                        >
                          <Zap className="w-4 h-4 mr-2" />
                          Match
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Success Dialog */}
      <Dialog open={showSuccessDialog} onOpenChange={setShowSuccessDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
                <Check className="w-6 h-6 text-green-600" />
              </div>
              Document Uploaded!
            </DialogTitle>
            <DialogDescription>
              {lastUploadedDoc && (
                <>
                  <strong>{lastUploadedDoc.filename}</strong> has been successfully processed.
                  <br />
                  {lastUploadedDoc.content.length} characters extracted.
                </>
              )}
            </DialogDescription>
          </DialogHeader>

          <div>
            <p className="font-semibold mb-3">What would you like to create?</p>
            <div className="grid grid-cols-1 gap-3">
              <Button
                variant="outline"
                className="h-16 justify-start"
                onClick={() => handleUseDocument('flashcards')}
              >
                <Brain className="w-5 h-5 mr-3 text-purple-500" />
                <div className="text-left">
                  <div className="font-medium">Generate Flashcards</div>
                  <div className="text-xs text-muted-foreground">
                    AI-powered flashcards with spaced repetition
                  </div>
                </div>
              </Button>

              <Button
                variant="outline"
                className="h-16 justify-start"
                onClick={() => handleUseDocument('quiz')}
              >
                <Target className="w-5 h-5 mr-3 text-blue-500" />
                <div className="text-left">
                  <div className="font-medium">Create Quiz</div>
                  <div className="text-xs text-muted-foreground">
                    Multiple choice questions to test knowledge
                  </div>
                </div>
              </Button>

              <Button
                variant="outline"
                className="h-16 justify-start"
                onClick={() => handleUseDocument('match')}
              >
                <Zap className="w-5 h-5 mr-3 text-emerald-500" />
                <div className="text-left">
                  <div className="font-medium">Play Match Game</div>
                  <div className="text-xs text-muted-foreground">
                    Match terms with definitions interactively
                  </div>
                </div>
              </Button>
            </div>
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowSuccessDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </ProjectLayout>
  );
}
