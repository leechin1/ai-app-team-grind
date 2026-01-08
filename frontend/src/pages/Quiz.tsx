import { useState, useEffect } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import {
  Target, Play, RotateCw, Trophy, CheckCircle2,
  XCircle, ChevronRight
} from "lucide-react";
import ProjectLayout from "@/components/ProjectLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { quizAPI, type QuizQuestion } from "@/lib/api";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

type ViewMode = 'menu' | 'generate' | 'browse' | 'taking' | 'results';

interface QuizState {
  quiz_id: string;
  questions: QuizQuestion[];
  answers: (number | null)[];
  currentQuestionIndex: number;
  questionStartTimes: number[]; // Track when each question was started
}

export default function Quiz() {
  const navigate = useNavigate();
  const location = useLocation();
  const { projectId } = useParams<{ projectId: string }>();
  const [viewMode, setViewMode] = useState<ViewMode>('menu');

  // Setup state
  const [content, setContent] = useState('');
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [sourceDocumentId, setSourceDocumentId] = useState<string | null>(null);
  const [sourceDocumentName, setSourceDocumentName] = useState<string | null>(null);

  // Selection state
  const [selectedQuestions, setSelectedQuestions] = useState<Set<string>>(new Set());

  // Fetch all quiz questions for selection
  const { data: questionsData, isLoading: questionsLoading } = useQuery({
    queryKey: ['quiz-questions', projectId],
    queryFn: () => {
      if (!projectId) throw new Error("No project selected");
      return quizAPI.list(projectId);
    },
    enabled: !!projectId,
  });

  const allQuestions = questionsData?.questions || [];

  // Check if content was passed from Upload page
  useEffect(() => {
    const state = location.state as any;
    const uploadedContent = state?.content;
    const documentId = state?.documentId;
    const documentName = state?.documentName;

    if (uploadedContent) {
      setContent(uploadedContent);
      if (documentId) {
        setSourceDocumentId(documentId);
        setSourceDocumentName(documentName);
      }
      setViewMode('generate');
      toast.info('PDF content loaded! Ready to generate quiz.');
    }
  }, [location.state]);

  // Quiz state
  const [quizState, setQuizState] = useState<QuizState | null>(null);

  // Generate quiz mutation
  const generateMutation = useMutation({
    mutationFn: (data: { content: string; num_questions: number; difficulty: string }) => {
      if (!projectId) {
        throw new Error("No project selected");
      }
      return quizAPI.generate(data, projectId);
    },
    onSuccess: (data) => {
      const now = Date.now();
      setQuizState({
        quiz_id: data.quiz_id,
        questions: data.questions,
        answers: new Array(data.questions.length).fill(null),
        currentQuestionIndex: 0,
        questionStartTimes: new Array(data.questions.length).fill(now),
      });
      setViewMode('taking');
      toast.success(`Quiz generated with ${data.questions.length} questions!`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to generate quiz: ${error.message}`);
    },
  });

  // Submit quiz mutation
  const submitMutation = useMutation({
    mutationFn: (data: { quiz_id: string; answers: any[] }) =>
      quizAPI.submit(data.quiz_id, data.answers),
    onSuccess: () => {
      setViewMode('results');
      toast.success('Quiz submitted successfully!');
    },
    onError: (error: Error) => {
      toast.error(`Failed to submit quiz: ${error.message}`);
    },
  });

  const handleGenerate = () => {
    if (!content.trim()) {
      toast.error('Please enter some content');
      return;
    }

    generateMutation.mutate({
      content,
      num_questions: numQuestions,
      difficulty,
      project_id: projectId,
      source_id: sourceDocumentId || undefined,
      source_name: sourceDocumentName || undefined,
    });
  };

  // Selection handlers
  const handleToggleQuestion = (questionId: string) => {
    const newSelection = new Set(selectedQuestions);
    if (newSelection.has(questionId)) {
      newSelection.delete(questionId);
    } else {
      newSelection.add(questionId);
    }
    setSelectedQuestions(newSelection);
  };

  const handleSelectAll = () => {
    if (selectedQuestions.size === allQuestions.length) {
      setSelectedQuestions(new Set());
    } else {
      setSelectedQuestions(new Set(allQuestions.map(q => q.id)));
    }
  };

  const handleStartQuiz = () => {
    if (selectedQuestions.size === 0) {
      toast.error('Please select at least one question');
      return;
    }

    const selectedQs = allQuestions.filter(q => selectedQuestions.has(q.id));
    const now = Date.now();
    setQuizState({
      quiz_id: `quiz_${Date.now()}`,
      questions: selectedQs,
      answers: new Array(selectedQs.length).fill(null),
      currentQuestionIndex: 0,
      questionStartTimes: new Array(selectedQs.length).fill(now),
    });
    setViewMode('taking');
  };

  const handleAnswerSelect = (answerIndex: number) => {
    if (!quizState) return;

    const newAnswers = [...quizState.answers];
    newAnswers[quizState.currentQuestionIndex] = answerIndex;
    
    // Record the time when answer was selected (if not already recorded)
    const newStartTimes = [...quizState.questionStartTimes];
    if (newStartTimes[quizState.currentQuestionIndex] === newStartTimes[0]) {
      // First time answering this question, record start time
      newStartTimes[quizState.currentQuestionIndex] = Date.now();
    }
    
    setQuizState({ ...quizState, answers: newAnswers, questionStartTimes: newStartTimes });
  };

  const handleNext = () => {
    if (!quizState) return;

    if (quizState.currentQuestionIndex < quizState.questions.length - 1) {
      setQuizState({
        ...quizState,
        currentQuestionIndex: quizState.currentQuestionIndex + 1,
      });
    }
  };

  const handlePrevious = () => {
    if (!quizState) return;

    if (quizState.currentQuestionIndex > 0) {
      setQuizState({
        ...quizState,
        currentQuestionIndex: quizState.currentQuestionIndex - 1,
      });
    }
  };

  const handleSubmit = () => {
    if (!quizState) return;

    const hasUnanswered = quizState.answers.some(a => a === null);
    if (hasUnanswered) {
      toast.error('Please answer all questions before submitting');
      return;
    }

    const now = Date.now();
    const answers = quizState.questions.map((q, i) => ({
      question_id: q.id,
      user_answer_index: quizState.answers[i]!,
      time_spent_seconds: (now - quizState.questionStartTimes[i]) / 1000,
    }));

    submitMutation.mutate({
      quiz_id: quizState.quiz_id,
      answers,
    });
  };

  const calculateScore = () => {
    if (!quizState) return 0;

    const correct = quizState.questions.filter((q, i) =>
      quizState.answers[i] === q.correct_answer_index
    ).length;

    return Math.round((correct / quizState.questions.length) * 100);
  };

  const currentQuestion = quizState?.questions[quizState.currentQuestionIndex];
  const currentAnswer = quizState?.answers[quizState.currentQuestionIndex];

  return (
    <ProjectLayout>
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Menu View */}
        {viewMode === 'menu' && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Quiz</h1>
              <p className="text-muted-foreground">
                Test your knowledge with AI-generated multiple choice quizzes
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setViewMode('browse')}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Play className="w-8 h-8 text-primary" />
                    <Badge className="bg-primary">{allQuestions.length} questions</Badge>
                  </div>
                  <CardTitle>Take Quiz</CardTitle>
                  <CardDescription>
                    Select quiz questions to test yourself
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setViewMode('generate')}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Target className="w-8 h-8 text-primary" />
                  </div>
                  <CardTitle>Generate Quiz</CardTitle>
                  <CardDescription>
                    Create new quiz questions from your study material
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>
        )}

        {/* Browse View - Select Questions */}
        {viewMode === 'browse' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">Select Quiz Questions</h2>
                <p className="text-muted-foreground">
                  Choose questions to include in your quiz
                </p>
              </div>
              <Button variant="outline" onClick={() => setViewMode('menu')}>
                Back
              </Button>
            </div>

            {questionsLoading ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <RotateCw className="w-12 h-12 animate-spin mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">Loading questions...</p>
                </CardContent>
              </Card>
            ) : allQuestions.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground mb-4">
                    No quiz questions available. Generate some questions first!
                  </p>
                  <Button onClick={() => setViewMode('generate')}>
                    Generate Questions
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <Button variant="outline" size="sm" onClick={handleSelectAll}>
                    {selectedQuestions.size === allQuestions.length ? 'Deselect All' : 'Select All'}
                  </Button>
                  <div className="text-sm text-muted-foreground">
                    {selectedQuestions.size} selected
                  </div>
                </div>

                <div className="space-y-2">
                  {allQuestions.map((question) => (
                    <Card key={question.id} className="hover:bg-accent/50 transition-colors">
                      <CardContent className="py-4">
                        <div className="flex items-start gap-4">
                          <Checkbox
                            checked={selectedQuestions.has(question.id)}
                            onCheckedChange={() => handleToggleQuestion(question.id)}
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1">
                                <p className="font-medium">{question.question}</p>
                                <div className="mt-2 space-y-1">
                                  {question.options.map((option, i) => (
                                    <p key={i} className={`text-sm ${i === question.correct_answer_index ? 'text-green-600 dark:text-green-400 font-medium' : 'text-muted-foreground'}`}>
                                      {String.fromCharCode(65 + i)}. {option}
                                    </p>
                                  ))}
                                </div>
                                {question.explanation && (
                                  <p className="text-sm text-muted-foreground mt-2 italic">
                                    {question.explanation}
                                  </p>
                                )}
                              </div>
                              <div className="text-right flex-shrink-0">
                                <Badge variant="outline" className="text-xs mb-2">
                                  {question.source_name || 'Manual'}
                                </Badge>
                                <Badge variant="outline" className="text-xs block">
                                  {question.difficulty}
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
                    onClick={handleStartQuiz}
                    disabled={selectedQuestions.size === 0}
                    size="lg"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Start Quiz ({selectedQuestions.size} questions)
                  </Button>
                </div>
              </>
            )}
          </div>
        )}

        {/* Generate View */}
        {viewMode === 'generate' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold mb-2">Generate Quiz</h2>
              <p className="text-muted-foreground">
                Create AI-powered multiple choice questions from your study material
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
                    <Label htmlFor="num-questions">Number of Questions</Label>
                    <Input
                      id="num-questions"
                      type="number"
                      min="1"
                      max="20"
                      value={numQuestions}
                      onChange={(e) => setNumQuestions(parseInt(e.target.value) || 5)}
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
                        Generating Quiz...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-2" />
                        Generate Quiz
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

        {/* Taking View */}
        {viewMode === 'taking' && quizState && currentQuestion && (
          <div className="space-y-6">
            <Progress
              value={((quizState.currentQuestionIndex + 1) / quizState.questions.length) * 100}
              className="h-2"
            />

            <Card>
              <CardHeader>
                <CardDescription>Question {quizState.currentQuestionIndex + 1} of {quizState.questions.length}</CardDescription>
                <CardTitle className="text-xl">{currentQuestion.question}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <RadioGroup value={currentAnswer?.toString() || ''} onValueChange={(v) => handleAnswerSelect(parseInt(v))}>
                  {currentQuestion.options.map((option, index) => (
                    <div key={index} className="flex items-center space-x-2 p-4 rounded-lg border border-border hover:bg-muted/50 cursor-pointer transition-colors">
                      <RadioGroupItem value={index.toString()} id={`option-${index}`} />
                      <Label htmlFor={`option-${index}`} className="flex-1 cursor-pointer">
                        {option}
                      </Label>
                    </div>
                  ))}
                </RadioGroup>

                <div className="flex gap-2 pt-4">
                  <Button
                    variant="outline"
                    onClick={handlePrevious}
                    disabled={quizState.currentQuestionIndex === 0}
                  >
                    Previous
                  </Button>

                  {quizState.currentQuestionIndex < quizState.questions.length - 1 ? (
                    <Button onClick={handleNext} className="flex-1">
                      Next <ChevronRight className="w-4 h-4 ml-2" />
                    </Button>
                  ) : (
                    <Button
                      onClick={handleSubmit}
                      className="flex-1"
                      disabled={submitMutation.isPending}
                    >
                      {submitMutation.isPending ? (
                        <>
                          <RotateCw className="w-4 h-4 mr-2 animate-spin" />
                          Submitting...
                        </>
                      ) : (
                        <>
                          <Trophy className="w-4 h-4 mr-2" />
                          Submit Quiz
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Question Navigator */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Question Navigator</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {quizState.questions.map((_, index) => (
                    <Button
                      key={index}
                      variant={index === quizState.currentQuestionIndex ? 'default' : 'outline'}
                      size="sm"
                      className="w-10 h-10"
                      onClick={() => setQuizState({ ...quizState, currentQuestionIndex: index })}
                    >
                      {quizState.answers[index] !== null && (
                        <CheckCircle2 className="w-3 h-3 absolute top-0 right-0 text-green-500" />
                      )}
                      {index + 1}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Results View */}
        {viewMode === 'results' && quizState && (
          <div className="space-y-6">
            <Card className="bg-gradient-to-br from-primary/10 to-primary/5">
              <CardContent className="pt-8 pb-8 text-center">
                <Trophy className="w-16 h-16 mx-auto mb-4 text-primary" />
                <h2 className="text-3xl font-bold mb-2">Quiz Complete!</h2>
                <p className="text-5xl font-bold text-primary mb-4">{calculateScore()}%</p>
                <p className="text-muted-foreground">
                  You got {quizState.questions.filter((q, i) => quizState.answers[i] === q.correct_answer_index).length} out of {quizState.questions.length} correct
                </p>
              </CardContent>
            </Card>

            {/* Review Answers */}
            <div className="space-y-4">
              <h3 className="text-xl font-bold">Review Your Answers</h3>
              {quizState.questions.map((question, index) => {
                const isCorrect = quizState.answers[index] === question.correct_answer_index;
                return (
                  <Card key={question.id} className={isCorrect ? 'border-green-500/50' : 'border-red-500/50'}>
                    <CardHeader>
                      <div className="flex items-start gap-2">
                        {isCorrect ? (
                          <CheckCircle2 className="w-5 h-5 text-green-500 mt-1" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-500 mt-1" />
                        )}
                        <div className="flex-1">
                          <CardDescription>Question {index + 1}</CardDescription>
                          <CardTitle className="text-lg">{question.question}</CardTitle>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="space-y-2">
                        {question.options.map((option, optionIndex) => {
                          const isUserAnswer = quizState.answers[index] === optionIndex;
                          const isCorrectAnswer = question.correct_answer_index === optionIndex;

                          return (
                            <div
                              key={optionIndex}
                              className={`p-3 rounded-lg ${
                                isCorrectAnswer
                                  ? 'bg-green-500/20 border border-green-500'
                                  : isUserAnswer
                                  ? 'bg-red-500/20 border border-red-500'
                                  : 'bg-muted'
                              }`}
                            >
                              {option}
                              {isCorrectAnswer && <span className="ml-2 text-green-600 font-medium">✓ Correct</span>}
                              {isUserAnswer && !isCorrectAnswer && <span className="ml-2 text-red-600 font-medium">✗ Your answer</span>}
                            </div>
                          );
                        })}
                      </div>
                      <div className="pt-2 text-sm text-muted-foreground">
                        <strong>Explanation:</strong> {question.explanation}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => {
                setViewMode('setup');
                setQuizState(null);
                setContent('');
              }}>
                Create New Quiz
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
