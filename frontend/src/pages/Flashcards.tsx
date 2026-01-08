import { useState, useEffect } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import {
  Brain, Play, Plus, RotateCw, Check, X,
  Clock, Flame, Target
} from "lucide-react";
import ProjectLayout from "@/components/ProjectLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { flashcardAPI, type FlashCard } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

type ViewMode = 'menu' | 'generate' | 'browse' | 'review';

export default function Flashcards() {
  const navigate = useNavigate();
  const location = useLocation();
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<ViewMode>('menu');
  const [selectedCards, setSelectedCards] = useState<Set<string>>(new Set());

  // Generation state
  const [content, setContent] = useState('');
  const [numCards, setNumCards] = useState(10);
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [filterDocumentId, setFilterDocumentId] = useState<string | null>(null);
  const [filterDocumentName, setFilterDocumentName] = useState<string | null>(null);

  // Check if content was passed from Upload page or Review page
  useEffect(() => {
    const state = location.state as any;
    const uploadedContent = state?.content;
    const documentId = state?.documentId;
    const documentName = state?.documentName;
    const reviewMode = state?.reviewMode;

    if (uploadedContent) {
      setContent(uploadedContent);
      setViewMode('generate');
      // Store source document info for tracking
      if (documentId) {
        setFilterDocumentId(documentId);
        setFilterDocumentName(documentName);
      }
      toast.info('PDF content loaded! Ready to generate flashcards.');
    }

    if (reviewMode && documentId) {
      setFilterDocumentId(documentId);
      setFilterDocumentName(documentName);
      setViewMode('review');
      toast.info(`Reviewing flashcards from "${documentName}"`);
    }
  }, [location.state]);

  // Review state
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [reviewStartTime, setReviewStartTime] = useState<number>(Date.now());

  // Fetch all flashcards for browsing
  const { data: allCardsData } = useQuery({
    queryKey: ['flashcards', projectId],
    queryFn: () => {
      if (!projectId) throw new Error("No project selected");
      return flashcardAPI.list(projectId);
    },
    enabled: !!projectId && viewMode === 'browse',
  });

  // Fetch due flashcards for review
  const { data: dueData, isLoading: dueLoading } = useQuery({
    queryKey: ['flashcards', 'due', projectId],
    queryFn: () => {
      if (!projectId) throw new Error("No project selected");
      return flashcardAPI.getDue(projectId);
    },
    enabled: !!projectId && viewMode === 'review',
  });

  const allCards = allCardsData?.flashcards || [];
  const dueCards = dueData?.due_cards || [];
  const currentCard = dueCards[currentCardIndex];

  // Generate flashcards mutation
  const generateMutation = useMutation({
    mutationFn: (data: { content: string; num_flashcards: number; difficulty: string }) => {
      if (!projectId) {
        throw new Error("No project selected");
      }
      return flashcardAPI.generate(data, projectId);
    },
    onSuccess: (data) => {
      toast.success(`Generated ${data.flashcards.length} flashcards!`);
      queryClient.invalidateQueries({ queryKey: ['flashcards'] });
      setContent('');
      setViewMode('menu');
    },
    onError: (error: Error) => {
      toast.error(`Failed to generate flashcards: ${error.message}`);
    },
  });

  // Review flashcard mutation
  const reviewMutation = useMutation({
    mutationFn: (data: {
      flashcard_id: string;
      response_quality: number;
      was_correct: boolean;
      time_spent_seconds: number;
    }) => flashcardAPI.review(data),
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ['flashcards'] });

      // Move to next card
      if (currentCardIndex < dueCards.length - 1) {
        setCurrentCardIndex(currentCardIndex + 1);
        setIsFlipped(false);
        setReviewStartTime(Date.now());
      } else {
        // Finished all due cards
        toast.success('All cards reviewed! Great job!');
        setViewMode('menu');
        setCurrentCardIndex(0);
      }
    },
    onError: (error: Error) => {
      toast.error(`Failed to save review: ${error.message}`);
    },
  });

  const handleGenerate = () => {
    if (!content.trim()) {
      toast.error('Please enter some content');
      return;
    }

    generateMutation.mutate({
      content,
      num_flashcards: numCards,
      difficulty,
      source_id: filterDocumentId || undefined,
      source_name: filterDocumentName || undefined,
    });
  };

  const handleReviewResponse = (quality: number, wasCorrect: boolean) => {
    if (!currentCard) return;

    const timeSpent = Math.round((Date.now() - reviewStartTime) / 1000);

    reviewMutation.mutate({
      flashcard_id: currentCard.id,
      response_quality: quality,
      was_correct: wasCorrect,
      time_spent_seconds: timeSpent,
    });
  };

  const getDifficultyColor = (diff: string) => {
    switch (diff) {
      case 'easy': return 'bg-green-500/20 text-green-700 dark:text-green-400';
      case 'medium': return 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400';
      case 'hard': return 'bg-red-500/20 text-red-700 dark:text-red-400';
      default: return 'bg-gray-500/20 text-gray-700 dark:text-gray-400';
    }
  };

  const getNextReviewDate = (card: FlashCard) => {
    if (!card.next_review_date) return null;
    
    const nextDate = new Date(card.next_review_date);
    const now = new Date();
    const diffTime = nextDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return "Review now";
    if (diffDays === 0) return "Review today";
    if (diffDays === 1) return "Review tomorrow";
    return `Review in ${diffDays} days`;
  };

  return (
    <ProjectLayout>
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Brain className="w-6 h-6 text-primary" />
                <span className="text-xl font-bold">Flashcards</span>
              </div>
            </div>
            {viewMode === 'review' && dueCards.length > 0 && (
              <div className="text-sm text-muted-foreground">
                Card {currentCardIndex + 1} of {dueCards.length}
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Menu View */}
        {viewMode === 'menu' && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Flashcards</h1>
              <p className="text-muted-foreground">
                AI-powered flashcards with SM-2 spaced repetition algorithm
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setViewMode('review')}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Play className="w-8 h-8 text-primary" />
                    {dueLoading ? (
                      <Badge variant="secondary">Loading...</Badge>
                    ) : (
                      <Badge className="bg-primary">{dueData?.total_due || 0} due</Badge>
                    )}
                  </div>
                  <CardTitle>Review Cards</CardTitle>
                  <CardDescription>
                    Review flashcards that are due for spaced repetition
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setViewMode('generate')}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Plus className="w-8 h-8 text-primary" />
                  </div>
                  <CardTitle>Generate Cards</CardTitle>
                  <CardDescription>
                    Create new flashcards from your study material
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>
        )}

        {/* Generate View */}
        {viewMode === 'generate' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold mb-2">Generate Flashcards</h2>
              <p className="text-muted-foreground">
                Paste your study material and let AI create flashcards for you
              </p>
            </div>

            <Card>
              <CardContent className="pt-6 space-y-4">
                <div>
                  <Label htmlFor="content">Study Material</Label>
                  <Textarea
                    id="content"
                    placeholder="Paste your notes, lecture content, or study material here..."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={12}
                    className="mt-2"
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    {content.length} characters
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="num-cards">Number of Cards</Label>
                    <Input
                      id="num-cards"
                      type="number"
                      min="1"
                      max="50"
                      value={numCards}
                      onChange={(e) => setNumCards(parseInt(e.target.value) || 10)}
                      className="mt-2"
                    />
                  </div>

                  <div>
                    <Label htmlFor="difficulty">Difficulty</Label>
                    <Select value={difficulty} onValueChange={(v) => setDifficulty(v as any)}>
                      <SelectTrigger id="difficulty" className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="easy">Easy</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="hard">Hard</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex gap-2 pt-4">
                  <Button
                    onClick={handleGenerate}
                    disabled={generateMutation.isPending || !content.trim()}
                    className="flex-1"
                  >
                    {generateMutation.isPending ? (
                      <>
                        <RotateCw className="w-4 h-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Flame className="w-4 h-4 mr-2" />
                        Generate Flashcards
                      </>
                    )}
                  </Button>
                  <Button variant="outline" onClick={() => setViewMode('menu')}>
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Review View */}
        {viewMode === 'review' && (
          <div className="space-y-6">
            {dueLoading ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <RotateCw className="w-12 h-12 animate-spin mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">Loading flashcards...</p>
                </CardContent>
              </Card>
            ) : dueCards.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Check className="w-12 h-12 mx-auto mb-4 text-green-500" />
                  <h3 className="text-xl font-semibold mb-2">All caught up!</h3>
                  <p className="text-muted-foreground mb-6">
                    No flashcards are due for review right now.
                  </p>
                  <Button onClick={() => setViewMode('menu')}>Back to Menu</Button>
                </CardContent>
              </Card>
            ) : currentCard ? (
              <>
                <Progress value={(currentCardIndex / dueCards.length) * 100} className="h-2" />

                <div 
                  className="perspective-1000 cursor-pointer min-h-[400px]"
                  onClick={() => setIsFlipped(!isFlipped)}
                >
                  <div 
                    className={`relative w-full h-[400px] transition-transform duration-700 transform-style-3d ${
                      isFlipped ? 'rotate-y-180' : ''
                    }`}
                    style={{
                      transformStyle: 'preserve-3d',
                      transition: 'transform 0.7s cubic-bezier(0.4, 0.0, 0.2, 1)',
                      transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
                    }}
                  >
                    {/* Front of card */}
                    <Card 
                      className={`absolute w-full h-full backface-hidden ${
                        isFlipped ? 'pointer-events-none' : ''
                      }`}
                      style={{ backfaceVisibility: 'hidden' }}
                    >
                      <CardContent className="text-center py-12 px-8 h-full flex flex-col justify-center">
                        <div className="mb-4">
                          <Badge className={getDifficultyColor(currentCard.difficulty)}>
                            {currentCard.difficulty}
                          </Badge>
                        </div>

                        <div className="text-2xl font-medium mb-4">
                          {currentCard.front}
                        </div>

                        <p className="text-sm text-muted-foreground">
                          Click to reveal answer
                        </p>

                        {currentCard.tags && currentCard.tags.length > 0 && (
                          <div className="flex flex-wrap gap-2 justify-center mt-6">
                            {currentCard.tags.map((tag, i) => (
                              <Badge key={i} variant="outline">{tag}</Badge>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    {/* Back of card */}
                    <Card 
                      className={`absolute w-full h-full backface-hidden ${
                        !isFlipped ? 'pointer-events-none' : ''
                      }`}
                      style={{ 
                        backfaceVisibility: 'hidden',
                        transform: 'rotateY(180deg)'
                      }}
                    >
                      <CardContent className="text-center py-12 px-8 h-full flex flex-col justify-center bg-primary/5">
                        <div className="mb-4">
                          <Badge className={getDifficultyColor(currentCard.difficulty)}>
                            {currentCard.difficulty}
                          </Badge>
                        </div>

                        <div className="text-2xl font-medium mb-4">
                          {currentCard.back}
                        </div>

                        <p className="text-sm text-muted-foreground">
                          Click to see question
                        </p>

                        {currentCard.tags && currentCard.tags.length > 0 && (
                          <div className="flex flex-wrap gap-2 justify-center mt-6">
                            {currentCard.tags.map((tag, i) => (
                              <Badge key={i} variant="outline">{tag}</Badge>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {isFlipped && (
                  <>
                    {/* Next Review Info */}
                    {currentCard.next_review_date && (
                      <Card className="bg-blue-500/10 border-blue-500/50">
                        <CardContent className="py-4 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Clock className="w-4 h-4 text-blue-500" />
                            <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
                              {getNextReviewDate(currentCard)}
                            </span>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    <Card>
                      <CardHeader>
                        <CardTitle>How well did you know this?</CardTitle>
                        <CardDescription>Your answer affects the next review date</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 gap-3">
                          <Button
                            variant="outline"
                            className="h-20 flex flex-col gap-2"
                            onClick={() => handleReviewResponse(1, false)}
                            disabled={reviewMutation.isPending}
                          >
                            <X className="w-6 h-6 text-red-500" />
                            <span>Didn't Know</span>
                          </Button>
                          <Button
                            variant="outline"
                            className="h-20 flex flex-col gap-2"
                            onClick={() => handleReviewResponse(3, true)}
                            disabled={reviewMutation.isPending}
                          >
                            <Check className="w-6 h-6 text-yellow-500" />
                            <span>Somewhat</span>
                          </Button>
                          <Button
                            variant="outline"
                            className="h-20 flex flex-col gap-2"
                            onClick={() => handleReviewResponse(4, true)}
                            disabled={reviewMutation.isPending}
                          >
                            <Check className="w-6 h-6 text-green-500" />
                            <span>Knew It</span>
                          </Button>
                          <Button
                            variant="outline"
                            className="h-20 flex flex-col gap-2"
                            onClick={() => handleReviewResponse(5, true)}
                            disabled={reviewMutation.isPending}
                          >
                            <Target className="w-6 h-6 text-primary" />
                            <span>Easy!</span>
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </>
                )}
              </>
            ) : null}
          </div>
        )}
      </main>
    </div>
    </ProjectLayout>
  );
}
