import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, BookOpen, Brain, Target, Zap, FileText, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { flashcardAPI, documentAPI } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

export default function Review() {
  const navigate = useNavigate();

  // Fetch all flashcards grouped by document
  const { data: flashcardsData, isLoading: flashcardsLoading } = useQuery({
    queryKey: ['flashcards-by-document'],
    queryFn: () => flashcardAPI.byDocument(),
  });

  // Fetch all uploaded documents
  const { data: documentsData, isLoading: documentsLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentAPI.list(),
  });

  const handleReviewFlashcards = (documentId: string, documentName: string) => {
    navigate('/flashcards', {
      state: {
        documentId,
        documentName,
        reviewMode: true
      }
    });
  };

  const handleGenerateQuiz = (documentId: string, documentName: string) => {
    navigate('/quiz', {
      state: {
        documentId,
        documentName
      }
    });
  };

  const handleGenerateMatch = (documentId: string, documentName: string) => {
    navigate('/match', {
      state: {
        documentId,
        documentName
      }
    });
  };

  const isLoading = flashcardsLoading || documentsLoading;

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
                <BookOpen className="w-6 h-6 text-primary" />
                <span className="text-xl font-bold">Review Materials</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Review Your Study Materials</h1>
            <p className="text-muted-foreground">
              Browse all your generated flashcards, quizzes, and match games organized by source document
            </p>
          </div>

          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading your materials...</p>
            </div>
          ) : (
            <Tabs defaultValue="by-document" className="w-full">
              <TabsList className="grid w-full grid-cols-2 max-w-md">
                <TabsTrigger value="by-document">By Document</TabsTrigger>
                <TabsTrigger value="all-content">All Content</TabsTrigger>
              </TabsList>

              {/* By Document Tab */}
              <TabsContent value="by-document" className="space-y-4 mt-6">
                {flashcardsData?.by_document && flashcardsData.by_document.length > 0 ? (
                  <div className="grid grid-cols-1 gap-6">
                    {flashcardsData.by_document.map((docGroup) => {
                      const isManual = docGroup.document_id === 'manual';

                      return (
                        <Card key={docGroup.document_id} className="hover:shadow-lg transition-shadow">
                          <CardHeader>
                            <div className="flex items-start justify-between">
                              <div className="flex items-center gap-3">
                                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                                  isManual ? 'bg-gray-500/10' : 'bg-primary/10'
                                }`}>
                                  <FileText className={`w-6 h-6 ${
                                    isManual ? 'text-gray-600' : 'text-primary'
                                  }`} />
                                </div>
                                <div>
                                  <CardTitle className="text-lg">{docGroup.document_name}</CardTitle>
                                  <CardDescription>
                                    {docGroup.count} flashcard{docGroup.count !== 1 ? 's' : ''} generated
                                  </CardDescription>
                                </div>
                              </div>
                              <Badge variant="outline" className="bg-blue-500/20">
                                {docGroup.count} items
                              </Badge>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-4">
                              {/* Preview of flashcards */}
                              {docGroup.flashcards.length > 0 && (
                                <div className="bg-muted/50 rounded-lg p-4">
                                  <p className="text-sm font-medium mb-2">Sample flashcard:</p>
                                  <p className="text-sm text-muted-foreground line-clamp-2">
                                    <strong>Q:</strong> {docGroup.flashcards[0].front}
                                  </p>
                                  <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                                    <strong>A:</strong> {docGroup.flashcards[0].back}
                                  </p>
                                </div>
                              )}

                              {/* Action buttons */}
                              <div className="flex flex-wrap gap-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleReviewFlashcards(docGroup.document_id, docGroup.document_name)}
                                  className="flex-1 min-w-[140px]"
                                >
                                  <Brain className="w-4 h-4 mr-2 text-purple-500" />
                                  Review Flashcards
                                  <ChevronRight className="w-4 h-4 ml-auto" />
                                </Button>

                                {!isManual && (
                                  <>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => handleGenerateQuiz(docGroup.document_id, docGroup.document_name)}
                                      className="flex-1 min-w-[140px]"
                                    >
                                      <Target className="w-4 h-4 mr-2 text-blue-500" />
                                      Generate Quiz
                                      <ChevronRight className="w-4 h-4 ml-auto" />
                                    </Button>

                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => handleGenerateMatch(docGroup.document_id, docGroup.document_name)}
                                      className="flex-1 min-w-[140px]"
                                    >
                                      <Zap className="w-4 h-4 mr-2 text-emerald-500" />
                                      Generate Match
                                      <ChevronRight className="w-4 h-4 ml-auto" />
                                    </Button>
                                  </>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                ) : (
                  <Card className="text-center py-12">
                    <CardContent>
                      <FileText className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                      <h3 className="text-lg font-semibold mb-2">No materials yet</h3>
                      <p className="text-muted-foreground mb-4">
                        Upload documents or generate flashcards to see them here
                      </p>
                      <div className="flex justify-center gap-2">
                        <Button onClick={() => navigate('/upload')}>
                          <FileText className="w-4 h-4 mr-2" />
                          Upload Material
                        </Button>
                        <Button variant="outline" onClick={() => navigate('/flashcards')}>
                          <Brain className="w-4 h-4 mr-2" />
                          Generate Flashcards
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* All Content Tab */}
              <TabsContent value="all-content" className="space-y-4 mt-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Flashcards Summary */}
                  <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate('/flashcards')}>
                    <CardHeader>
                      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center mb-2">
                        <Brain className="w-6 h-6 text-white" />
                      </div>
                      <CardTitle>Flashcards</CardTitle>
                      <CardDescription>
                        {flashcardsData?.total || 0} total flashcards
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button variant="outline" className="w-full">
                        View All Flashcards
                        <ChevronRight className="w-4 h-4 ml-auto" />
                      </Button>
                    </CardContent>
                  </Card>

                  {/* Quizzes Summary */}
                  <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate('/quiz')}>
                    <CardHeader>
                      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mb-2">
                        <Target className="w-6 h-6 text-white" />
                      </div>
                      <CardTitle>Quizzes</CardTitle>
                      <CardDescription>
                        Test your knowledge
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button variant="outline" className="w-full">
                        Create New Quiz
                        <ChevronRight className="w-4 h-4 ml-auto" />
                      </Button>
                    </CardContent>
                  </Card>

                  {/* Match Games Summary */}
                  <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate('/match')}>
                    <CardHeader>
                      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mb-2">
                        <Zap className="w-6 h-6 text-white" />
                      </div>
                      <CardTitle>Match Games</CardTitle>
                      <CardDescription>
                        Interactive matching
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button variant="outline" className="w-full">
                        Create Match Game
                        <ChevronRight className="w-4 h-4 ml-auto" />
                      </Button>
                    </CardContent>
                  </Card>
                </div>

                {/* Documents List */}
                {documentsData && documentsData.documents.length > 0 && (
                  <div className="mt-8">
                    <h2 className="text-xl font-bold mb-4">All Uploaded Documents</h2>
                    <div className="grid grid-cols-1 gap-4">
                      {documentsData.documents.map((doc) => (
                        <Card key={doc.id} className="hover:shadow-lg transition-shadow">
                          <CardHeader>
                            <div className="flex items-start justify-between">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                                  <FileText className="w-5 h-5 text-primary" />
                                </div>
                                <div>
                                  <CardTitle className="text-base">{doc.filename}</CardTitle>
                                  <CardDescription>
                                    Uploaded {new Date(doc.uploaded_at).toLocaleDateString()}
                                  </CardDescription>
                                </div>
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                              {doc.preview}
                            </p>
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleReviewFlashcards(doc.id, doc.filename)}
                              >
                                <Brain className="w-4 h-4 mr-2" />
                                Flashcards
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleGenerateQuiz(doc.id, doc.filename)}
                              >
                                <Target className="w-4 h-4 mr-2" />
                                Quiz
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleGenerateMatch(doc.id, doc.filename)}
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
              </TabsContent>
            </Tabs>
          )}
        </div>
      </main>
    </div>
  );
}
