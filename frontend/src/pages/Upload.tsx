import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, ArrowLeft, Upload as UploadIcon, File, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { documentAPI } from "@/lib/api";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

export default function Upload() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadedContent, setUploadedContent] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentAPI.upload(file),
    onSuccess: (data) => {
      setUploadedContent(data.content);
      setFileName(data.filename);
      toast.success(`File "${data.filename}" uploaded successfully!`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to upload file: ${error.message}`);
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    uploadMutation.mutate(file);
  };

  const handleUseContent = (destination: 'flashcards' | 'quiz' | 'match') => {
    if (!uploadedContent) return;

    // Navigate to the destination with the content
    navigate(`/${destination}`, { state: { content: uploadedContent } });
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => navigate('/study')}>
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <div className="flex items-center gap-2">
                <FileText className="w-6 h-6 text-primary" />
                <span className="text-xl font-bold">Upload Material</span>
              </div>
            </div>
          </div>
        </div>
      </header>

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
                className="border-2 border-dashed border-border rounded-lg p-12 text-center cursor-pointer hover:border-primary/50 transition-colors"
                onClick={() => fileInputRef.current?.click()}
              >
                <UploadIcon className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">
                  {uploadMutation.isPending ? 'Uploading...' : 'Click to upload'}
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
              />
            </CardContent>
          </Card>

          {/* Success Card */}
          {uploadedContent && fileName && (
            <Card className="border-green-500/50">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-500" />
                  <CardTitle>File Uploaded Successfully</CardTitle>
                </div>
                <CardDescription>
                  <File className="w-4 h-4 inline mr-2" />
                  {fileName}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Content preview:</p>
                  <div className="bg-muted p-4 rounded-lg max-h-48 overflow-y-auto">
                    <p className="text-sm whitespace-pre-wrap">
                      {uploadedContent.substring(0, 500)}
                      {uploadedContent.length > 500 && '...'}
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    {uploadedContent.length} characters extracted
                  </p>
                </div>

                <div>
                  <p className="font-semibold mb-3">What would you like to create?</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <Button
                      variant="outline"
                      className="h-20 flex flex-col gap-2"
                      onClick={() => handleUseContent('flashcards')}
                    >
                      <span className="text-2xl">🧠</span>
                      <span>Flashcards</span>
                    </Button>
                    <Button
                      variant="outline"
                      className="h-20 flex flex-col gap-2"
                      onClick={() => handleUseContent('quiz')}
                    >
                      <span className="text-2xl">🎯</span>
                      <span>Quiz</span>
                    </Button>
                    <Button
                      variant="outline"
                      className="h-20 flex flex-col gap-2"
                      onClick={() => handleUseContent('match')}
                    >
                      <span className="text-2xl">⚡</span>
                      <span>Match Game</span>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
