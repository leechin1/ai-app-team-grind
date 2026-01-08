import { useState, useEffect } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import {
  Zap, Play, RotateCw, Trophy, Shuffle
} from "lucide-react";
import ProjectLayout from "@/components/ProjectLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { matchAPI, flashcardAPI, type MatchPair, type FlashCard } from "@/lib/api";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

type ViewMode = 'menu' | 'selectFlashcards' | 'playing' | 'results';

interface MatchState {
  match_quiz_id: string;
  pairs: MatchPair[];
  shuffledAnswers: { index: number; text: string }[];
  matches: Map<number, number>; // promptIndex -> answerIndex
  selectedPrompt: number | null;
  selectedAnswer: number | null;
  startTime: number;
  endTime: number | null;
}

export default function MatchQuiz() {
  const navigate = useNavigate();
  const location = useLocation();
  const { projectId } = useParams<{ projectId: string }>();
  const [viewMode, setViewMode] = useState<ViewMode>('menu');

  // Selection state
  const [selectedFlashcards, setSelectedFlashcards] = useState<Set<string>>(new Set());

  // Fetch all flashcards for selection
  const { data: flashcardsData, isLoading: flashcardsLoading } = useQuery({
    queryKey: ['flashcards', projectId],
    queryFn: () => {
      if (!projectId) throw new Error("No project selected");
      return flashcardAPI.list(projectId);
    },
    enabled: !!projectId,
  });

  const allFlashcards = flashcardsData?.flashcards || [];

  // Match state
  const [matchState, setMatchState] = useState<MatchState | null>(null);

  // Start game with selected flashcards
  const handleStartMatch = () => {
    if (selectedFlashcards.size === 0) {
      toast.error('Please select at least one flashcard');
      return;
    }

    // Convert selected flashcards to match pairs
    const selectedCards = allFlashcards.filter(card => selectedFlashcards.has(card.id));
    const pairs: MatchPair[] = selectedCards.map(card => ({
      id: card.id,
      prompt: card.front,
      answer: card.back,
      tags: card.tags || [],
    }));

    // Shuffle answers
    const shuffledAnswers = pairs
      .map((pair, index) => ({ index, text: pair.answer }))
      .sort(() => Math.random() - 0.5);

    setMatchState({
      match_quiz_id: `match_${Date.now()}`,
      pairs,
      shuffledAnswers,
      matches: new Map(),
      selectedPrompt: null,
      selectedAnswer: null,
      startTime: Date.now(),
      endTime: null,
    });
    setViewMode('playing');
    toast.success(`Match quiz started with ${pairs.length} pairs!`);
  };

  // Selection handlers
  const handleToggleFlashcard = (cardId: string) => {
    const newSelection = new Set(selectedFlashcards);
    if (newSelection.has(cardId)) {
      newSelection.delete(cardId);
    } else {
      newSelection.add(cardId);
    }
    setSelectedFlashcards(newSelection);
  };

  const handleSelectAll = () => {
    if (selectedFlashcards.size === allFlashcards.length) {
      setSelectedFlashcards(new Set());
    } else {
      setSelectedFlashcards(new Set(allFlashcards.map(c => c.id)));
    }
  };

  const handlePromptClick = (index: number) => {
    if (!matchState) return;

    // If already matched, do nothing
    if (matchState.matches.has(index)) return;

    if (matchState.selectedPrompt === index) {
      // Deselect
      setMatchState({ ...matchState, selectedPrompt: null });
    } else {
      setMatchState({ ...matchState, selectedPrompt: index });

      // If answer is selected, make the match
      if (matchState.selectedAnswer !== null) {
        makeMatch(index, matchState.selectedAnswer);
      }
    }
  };

  const handleAnswerClick = (answerShuffledIndex: number) => {
    if (!matchState) return;

    // Check if this answer is already matched
    const isMatched = Array.from(matchState.matches.values()).includes(answerShuffledIndex);
    if (isMatched) return;

    if (matchState.selectedAnswer === answerShuffledIndex) {
      // Deselect
      setMatchState({ ...matchState, selectedAnswer: null });
    } else {
      setMatchState({ ...matchState, selectedAnswer: answerShuffledIndex });

      // If prompt is selected, make the match
      if (matchState.selectedPrompt !== null) {
        makeMatch(matchState.selectedPrompt, answerShuffledIndex);
      }
    }
  };

  const makeMatch = (promptIndex: number, answerShuffledIndex: number) => {
    if (!matchState) return;

    const newMatches = new Map(matchState.matches);
    newMatches.set(promptIndex, answerShuffledIndex);

    setMatchState({
      ...matchState,
      matches: newMatches,
      selectedPrompt: null,
      selectedAnswer: null,
    });

    // Check if all matched
    if (newMatches.size === matchState.pairs.length) {
      finishQuiz(newMatches);
    }
  };

  const finishQuiz = (matches: Map<number, number>) => {
    if (!matchState) return;

    const endTime = Date.now();
    const totalTime = (endTime - matchState.startTime) / 1000;
    const timePerMatch = totalTime / matches.size;
    
    setMatchState({ ...matchState, endTime, matches });

    // Submit to backend with correct field names
    const answers = Array.from(matches.entries()).map(([promptIndex, answerShuffledIndex]) => ({
      pair_id: matchState.pairs[promptIndex].id,
      user_matched_index: matchState.shuffledAnswers[answerShuffledIndex].index,
      time_spent_seconds: timePerMatch,
    }));

    submitMutation.mutate({
      match_quiz_id: matchState.match_quiz_id,
      answers,
    });

    setViewMode('results');
  };

  const calculateScore = () => {
    if (!matchState) return { correct: 0, total: 0, percentage: 0 };

    let correct = 0;
    matchState.matches.forEach((answerShuffledIndex, promptIndex) => {
      const actualAnswerIndex = matchState.shuffledAnswers[answerShuffledIndex].index;
      if (actualAnswerIndex === promptIndex) {
        correct++;
      }
    });

    return {
      correct,
      total: matchState.pairs.length,
      percentage: Math.round((correct / matchState.pairs.length) * 100),
    };
  };

  const getElapsedTime = () => {
    if (!matchState) return 0;
    const end = matchState.endTime || Date.now();
    return Math.round((end - matchState.startTime) / 1000);
  };

  const isPromptMatched = (index: number) => matchState?.matches.has(index);
  const isAnswerMatched = (shuffledIndex: number) =>
    matchState ? Array.from(matchState.matches.values()).includes(shuffledIndex) : false;

  return (
    <ProjectLayout>
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Menu View */}
        {viewMode === 'menu' && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Match Quiz</h1>
              <p className="text-muted-foreground">
                Match terms with their definitions in this interactive game
              </p>
            </div>

            <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setViewMode('selectFlashcards')}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Zap className="w-8 h-8 text-primary" />
                  <Badge className="bg-primary">{allFlashcards.length} cards</Badge>
                </div>
                <CardTitle>Start Match Quiz</CardTitle>
                <CardDescription>
                  Select flashcards to create a matching game
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        )}

        {/* Select Flashcards View */}
        {viewMode === 'selectFlashcards' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">Select Flashcards</h2>
                <p className="text-muted-foreground">
                  Choose flashcards to include in your match quiz
                </p>
              </div>
              <Button variant="outline" onClick={() => setViewMode('menu')}>
                Back
              </Button>
            </div>

            {flashcardsLoading ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <RotateCw className="w-12 h-12 animate-spin mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">Loading flashcards...</p>
                </CardContent>
              </Card>
            ) : allFlashcards.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground mb-4">
                    No flashcards available. Create some flashcards first!
                  </p>
                  <Button onClick={() => navigate(`/project/${projectId}/flashcards`)}>
                    Go to Flashcards
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <Button variant="outline" size="sm" onClick={handleSelectAll}>
                    {selectedFlashcards.size === allFlashcards.length ? 'Deselect All' : 'Select All'}
                  </Button>
                  <div className="text-sm text-muted-foreground">
                    {selectedFlashcards.size} selected
                  </div>
                </div>

                <div className="space-y-2">
                  {allFlashcards.map((card) => (
                    <Card key={card.id} className="hover:bg-accent/50 transition-colors">
                      <CardContent className="py-4">
                        <div className="flex items-start gap-4">
                          <Checkbox
                            checked={selectedFlashcards.has(card.id)}
                            onCheckedChange={() => handleToggleFlashcard(card.id)}
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1">
                                <p className="font-medium">{card.front}</p>
                                <p className="text-sm text-muted-foreground mt-1">{card.back}</p>
                              </div>
                              <div className="text-right flex-shrink-0">
                                <Badge variant="outline" className="text-xs">
                                  {card.source_name || 'Manual'}
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                <div className="flex justify-end">
                  <Button
                    onClick={handleStartMatch}
                    disabled={selectedFlashcards.size === 0}
                    size="lg"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Start Match Quiz ({selectedFlashcards.size} pairs)
                  </Button>
                </div>
              </>
            )}
          </div>
        )}

        {/* Playing View */}
        {viewMode === 'playing' && matchState && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Match the terms with their definitions</CardTitle>
                <CardDescription>
                  Click on a term, then click on its matching definition. Time: {getElapsedTime()}s
                </CardDescription>
              </CardHeader>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Prompts Column */}
              <div className="space-y-3">
                <h3 className="font-semibold text-sm text-muted-foreground">Terms</h3>
                {matchState.pairs.map((pair, index) => (
                  <Card
                    key={index}
                    className={`cursor-pointer transition-all ${
                      isPromptMatched(index)
                        ? 'bg-green-500/20 border-green-500 opacity-60'
                        : matchState.selectedPrompt === index
                        ? 'border-primary border-2 shadow-lg'
                        : 'hover:border-primary/50'
                    }`}
                    onClick={() => handlePromptClick(index)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-2">
                        <p className="flex-1">{pair.prompt}</p>
                        {isPromptMatched(index) && (
                          <Badge variant="outline" className="bg-green-500/20">✓</Badge>
                        )}
                      </div>
                      {pair.tags && pair.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {pair.tags.map((tag, i) => (
                            <Badge key={i} variant="secondary" className="text-xs">{tag}</Badge>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Answers Column */}
              <div className="space-y-3">
                <h3 className="font-semibold text-sm text-muted-foreground">Definitions</h3>
                {matchState.shuffledAnswers.map((answer, shuffledIndex) => (
                  <Card
                    key={shuffledIndex}
                    className={`cursor-pointer transition-all ${
                      isAnswerMatched(shuffledIndex)
                        ? 'bg-green-500/20 border-green-500 opacity-60'
                        : matchState.selectedAnswer === shuffledIndex
                        ? 'border-primary border-2 shadow-lg'
                        : 'hover:border-primary/50'
                    }`}
                    onClick={() => handleAnswerClick(shuffledIndex)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-2">
                        <p className="flex-1">{answer.text}</p>
                        {isAnswerMatched(shuffledIndex) && (
                          <Badge variant="outline" className="bg-green-500/20">✓</Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Results View */}
        {viewMode === 'results' && matchState && (
          <div className="space-y-6">
            <Card className="bg-gradient-to-br from-primary/10 to-primary/5">
              <CardContent className="pt-8 pb-8 text-center">
                <Trophy className="w-16 h-16 mx-auto mb-4 text-primary" />
                <h2 className="text-3xl font-bold mb-2">Quiz Complete!</h2>
                <p className="text-5xl font-bold text-primary mb-2">{calculateScore().percentage}%</p>
                <p className="text-muted-foreground mb-4">
                  You got {calculateScore().correct} out of {calculateScore().total} correct
                </p>
                <p className="text-sm text-muted-foreground">
                  Completed in {getElapsedTime()} seconds
                </p>
              </CardContent>
            </Card>

            {/* Review Matches */}
            <div className="space-y-4">
              <h3 className="text-xl font-bold">Review Your Matches</h3>
              {matchState.pairs.map((pair, promptIndex) => {
                const answerShuffledIndex = matchState.matches.get(promptIndex);
                const selectedAnswer = answerShuffledIndex !== undefined
                  ? matchState.shuffledAnswers[answerShuffledIndex].text
                  : '';
                const isCorrect = answerShuffledIndex !== undefined &&
                  matchState.shuffledAnswers[answerShuffledIndex].index === promptIndex;

                return (
                  <Card key={pair.id} className={isCorrect ? 'border-green-500/50' : 'border-red-500/50'}>
                    <CardContent className="pt-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Term</p>
                          <p className="font-medium">{pair.prompt}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">
                            {isCorrect ? 'Correct Match ✓' : 'Your Match ✗'}
                          </p>
                          <p className={isCorrect ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                            {selectedAnswer}
                          </p>
                          {!isCorrect && (
                            <div className="mt-2">
                              <p className="text-sm text-muted-foreground">Correct answer:</p>
                              <p className="text-green-600 font-medium">{pair.answer}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => {
                setViewMode('setup');
                setMatchState(null);
                setContent('');
              }}>
                Create New Match Quiz
              </Button>
              <Button onClick={() => navigate('/study')}>
                Back to Study Hub
              </Button>
            </div>
          </div>
        )}
      </main>
    </ProjectLayout>
  );
}
