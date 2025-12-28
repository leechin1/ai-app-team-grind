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
import { matchAPI, type MatchPair } from "@/lib/api";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

type ViewMode = 'setup' | 'playing' | 'results';

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
  const [viewMode, setViewMode] = useState<ViewMode>('setup');
  const [useExistingFlashcards, setUseExistingFlashcards] = useState(true);

  // Setup state
  const [content, setContent] = useState('');
  const [numPairs, setNumPairs] = useState(5);
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');

  // Check if content was passed from Upload page
  useEffect(() => {
    const uploadedContent = (location.state as any)?.content;
    if (uploadedContent) {
      setContent(uploadedContent);
      setUseExistingFlashcards(false);
      toast.info('PDF content loaded! Ready to generate match quiz.');
    }
  }, [location.state]);

  // Match state
  const [matchState, setMatchState] = useState<MatchState | null>(null);

  // Generate match quiz mutation
  const generateMutation = useMutation({
    mutationFn: (data: { content: string; num_pairs: number; difficulty: string }) =>
      matchAPI.generate(data),
    onSuccess: (data) => {
      // Shuffle answers
      const shuffledAnswers = data.pairs
        .map((pair, index) => ({ index, text: pair.answer }))
        .sort(() => Math.random() - 0.5);

      setMatchState({
        match_quiz_id: data.match_quiz_id,
        pairs: data.pairs,
        shuffledAnswers,
        matches: new Map(),
        selectedPrompt: null,
        selectedAnswer: null,
        startTime: Date.now(),
        endTime: null,
      });
      setViewMode('playing');
      toast.success(`Match quiz generated with ${data.pairs.length} pairs!`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to generate match quiz: ${error.message}`);
    },
  });

  // Submit match quiz mutation
  const submitMutation = useMutation({
    mutationFn: (data: { match_quiz_id: string; answers: any[] }) =>
      matchAPI.submit(data.match_quiz_id, data.answers),
    onSuccess: () => {
      toast.success('Match quiz submitted successfully!');
    },
    onError: (error: Error) => {
      toast.error(`Failed to submit match quiz: ${error.message}`);
    },
  });

  const handleGenerate = () => {
    if (!useExistingFlashcards && !content.trim()) {
      toast.error('Please enter some content or use existing flashcards');
      return;
    }

    generateMutation.mutate({
      content: useExistingFlashcards ? '' : content,
      num_pairs: numPairs,
      difficulty,
      project_id: projectId,
    });
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
        {/* Setup View */}
        {viewMode === 'setup' && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Create a Match Quiz</h1>
              <p className="text-muted-foreground">
                Match terms with their definitions in this interactive game
              </p>
            </div>

            <Card>
              <CardContent className="pt-6 space-y-4">
                <div className="flex items-center space-x-2 mb-4">
                  <input
                    type="checkbox"
                    id="use-flashcards"
                    checked={useExistingFlashcards}
                    onChange={(e) => setUseExistingFlashcards(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <Label htmlFor="use-flashcards" className="cursor-pointer">
                    Use existing flashcards (recommended)
                  </Label>
                </div>

                {!useExistingFlashcards && (
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
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="num-pairs">Number of Pairs</Label>
                    <Input
                      id="num-pairs"
                      type="number"
                      min="1"
                      max="15"
                      value={numPairs}
                      onChange={(e) => setNumPairs(parseInt(e.target.value) || 5)}
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
                    disabled={generateMutation.isPending || (!useExistingFlashcards && !content.trim())}
                    className="flex-1"
                  >
                    {generateMutation.isPending ? (
                      <>
                        <RotateCw className="w-4 h-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-2" />
                        Generate Match Quiz
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
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
