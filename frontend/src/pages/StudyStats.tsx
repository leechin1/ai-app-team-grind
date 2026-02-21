import { useParams, useNavigate } from "react-router-dom";
import {
  BarChart3,
  Brain,
  Target,
  Zap,
  Flame,
  Trophy,
  BookOpen,
  FileText,
  FolderOpen,
  CheckCircle2,
  Clock,
} from "lucide-react";
import ProjectLayout from "@/components/ProjectLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { statsAPI } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export default function StudyStats() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const { data: stats, isLoading } = useQuery({
    queryKey: ["study-stats", projectId],
    queryFn: () => statsAPI.getProjectStats(projectId!),
    enabled: !!projectId,
    refetchInterval: 30000,
  });

  const maxDayReviews = stats
    ? Math.max(...stats.recent_activity.map((d) => d.reviews), 1)
    : 1;

  return (
    <ProjectLayout>
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-6 h-6 text-primary" />
                <span className="text-xl font-bold">Study Stats</span>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Your Study Progress</h1>
              <p className="text-muted-foreground">
                Track your learning streak, review activity, and overall performance
              </p>
            </div>

            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading your stats...</p>
              </div>
            ) : stats ? (
              <>
                {/* Streak & Key Metrics Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Current Streak */}
                  <Card className="border-orange-500/20 bg-gradient-to-br from-orange-500/5 to-amber-500/5">
                    <CardHeader className="pb-2">
                      <CardDescription className="flex items-center gap-2">
                        <Flame className="w-4 h-4 text-orange-500" />
                        Current Streak
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-bold text-orange-500">
                          {stats.current_streak}
                        </span>
                        <span className="text-muted-foreground text-sm">
                          {stats.current_streak === 1 ? "day" : "days"}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        Best: {stats.best_streak} {stats.best_streak === 1 ? "day" : "days"}
                      </p>
                    </CardContent>
                  </Card>

                  {/* Reviews Today */}
                  <Card className="border-blue-500/20 bg-gradient-to-br from-blue-500/5 to-cyan-500/5">
                    <CardHeader className="pb-2">
                      <CardDescription className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-blue-500" />
                        Reviewed Today
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-bold text-blue-500">
                          {stats.reviews_today}
                        </span>
                        <span className="text-muted-foreground text-sm">cards</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {stats.correct_today} correct today
                      </p>
                    </CardContent>
                  </Card>

                  {/* Accuracy */}
                  <Card className="border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 to-teal-500/5">
                    <CardHeader className="pb-2">
                      <CardDescription className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        Accuracy
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-bold text-emerald-500">
                          {stats.accuracy}%
                        </span>
                      </div>
                      <Progress
                        value={stats.accuracy}
                        className="mt-2 h-2 bg-emerald-500/10 [&>div]:bg-emerald-500"
                      />
                    </CardContent>
                  </Card>

                  {/* Due Cards */}
                  <Card className="border-purple-500/20 bg-gradient-to-br from-purple-500/5 to-indigo-500/5">
                    <CardHeader className="pb-2">
                      <CardDescription className="flex items-center gap-2">
                        <Brain className="w-4 h-4 text-purple-500" />
                        Due for Review
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-bold text-purple-500">
                          {stats.due_flashcards}
                        </span>
                        <span className="text-muted-foreground text-sm">cards</span>
                      </div>
                      {stats.due_flashcards > 0 && (
                        <Button
                          variant="link"
                          className="p-0 h-auto text-xs text-purple-500"
                          onClick={() => navigate(`/project/${projectId}/flashcards`)}
                        >
                          Start reviewing
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Weekly Activity Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Weekly Activity</CardTitle>
                    <CardDescription>
                      Your review activity over the last 7 days
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-end justify-between gap-2 h-40">
                      {stats.recent_activity.map((day) => {
                        const height = day.reviews > 0
                          ? Math.max((day.reviews / maxDayReviews) * 100, 8)
                          : 4;
                        const correctRatio = day.reviews > 0
                          ? (day.correct / day.reviews) * 100
                          : 0;
                        const isToday = day.date === new Date().toISOString().split("T")[0];

                        return (
                          <div
                            key={day.date}
                            className="flex-1 flex flex-col items-center gap-2"
                          >
                            <span className="text-xs text-muted-foreground">
                              {day.reviews > 0 ? day.reviews : ""}
                            </span>
                            <div className="w-full flex flex-col items-center">
                              <div
                                className={`w-full max-w-[40px] rounded-t-md transition-all ${
                                  day.reviews > 0
                                    ? "bg-primary/80"
                                    : "bg-muted"
                                }`}
                                style={{ height: `${height}%` }}
                                title={`${day.reviews} reviews, ${day.correct} correct (${Math.round(correctRatio)}%)`}
                              />
                            </div>
                            <span
                              className={`text-xs ${
                                isToday
                                  ? "font-bold text-primary"
                                  : "text-muted-foreground"
                              }`}
                            >
                              {isToday ? "Today" : day.day_label}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* Content Summary */}
                <div>
                  <h2 className="text-xl font-bold mb-4">Content Summary</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                    <Card className="hover:shadow-lg transition-shadow cursor-pointer"
                      onClick={() => navigate(`/project/${projectId}/flashcards`)}
                    >
                      <CardHeader className="pb-2">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center mb-1">
                          <Brain className="w-5 h-5 text-white" />
                        </div>
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Flashcards
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <span className="text-2xl font-bold">
                          {stats.counts.total_flashcards}
                        </span>
                      </CardContent>
                    </Card>

                    <Card className="hover:shadow-lg transition-shadow cursor-pointer"
                      onClick={() => navigate(`/project/${projectId}/quiz`)}
                    >
                      <CardHeader className="pb-2">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mb-1">
                          <Target className="w-5 h-5 text-white" />
                        </div>
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Quiz Questions
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <span className="text-2xl font-bold">
                          {stats.counts.total_quiz_questions}
                        </span>
                      </CardContent>
                    </Card>

                    <Card className="hover:shadow-lg transition-shadow cursor-pointer"
                      onClick={() => navigate(`/project/${projectId}/match`)}
                    >
                      <CardHeader className="pb-2">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mb-1">
                          <Zap className="w-5 h-5 text-white" />
                        </div>
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Match Pairs
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <span className="text-2xl font-bold">
                          {stats.counts.total_match_pairs}
                        </span>
                      </CardContent>
                    </Card>

                    <Card className="hover:shadow-lg transition-shadow cursor-pointer"
                      onClick={() => navigate(`/project/${projectId}/files`)}
                    >
                      <CardHeader className="pb-2">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mb-1">
                          <FolderOpen className="w-5 h-5 text-white" />
                        </div>
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Documents
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <span className="text-2xl font-bold">
                          {stats.counts.total_documents}
                        </span>
                      </CardContent>
                    </Card>

                    <Card className="hover:shadow-lg transition-shadow cursor-pointer"
                      onClick={() => navigate(`/project/${projectId}`)}
                    >
                      <CardHeader className="pb-2">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center mb-1">
                          <FileText className="w-5 h-5 text-white" />
                        </div>
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Notes
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <span className="text-2xl font-bold">
                          {stats.counts.total_notes}
                        </span>
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {/* Performance Overview */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Trophy className="w-5 h-5 text-amber-500" />
                      Performance Overview
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div>
                        <p className="text-sm text-muted-foreground mb-1">Total Reviews</p>
                        <p className="text-2xl font-bold">{stats.total_reviews}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground mb-1">Average Quality</p>
                        <div className="flex items-baseline gap-2">
                          <p className="text-2xl font-bold">{stats.average_quality}</p>
                          <span className="text-sm text-muted-foreground">/ 5</span>
                        </div>
                        <Progress
                          value={(stats.average_quality / 5) * 100}
                          className="mt-2 h-2"
                        />
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground mb-1">Mastery Level</p>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant="outline"
                            className={
                              stats.accuracy >= 80
                                ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30"
                                : stats.accuracy >= 50
                                ? "bg-amber-500/10 text-amber-600 border-amber-500/30"
                                : "bg-red-500/10 text-red-600 border-red-500/30"
                            }
                          >
                            {stats.accuracy >= 80
                              ? "Advanced"
                              : stats.accuracy >= 50
                              ? "Intermediate"
                              : stats.total_reviews === 0
                              ? "Not started"
                              : "Beginner"}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Empty state call-to-action if no reviews */}
                {stats.total_reviews === 0 && (
                  <Card className="text-center py-8">
                    <CardContent>
                      <BookOpen className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                      <h3 className="text-lg font-semibold mb-2">No reviews yet</h3>
                      <p className="text-muted-foreground mb-4">
                        Start reviewing flashcards to build your streak and track progress
                      </p>
                      <div className="flex justify-center gap-2">
                        <Button onClick={() => navigate(`/project/${projectId}/flashcards`)}>
                          <Brain className="w-4 h-4 mr-2" />
                          Start Studying
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : (
              <Card className="text-center py-12">
                <CardContent>
                  <BarChart3 className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-semibold mb-2">Could not load stats</h3>
                  <p className="text-muted-foreground">Please try again later</p>
                </CardContent>
              </Card>
            )}
          </div>
        </main>
      </div>
    </ProjectLayout>
  );
}
