import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Brain, BookOpen, Target, BarChart3, FileText,
  Settings, ArrowLeft, Clock, TrendingUp, Zap
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { healthAPI, statsAPI } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

export default function StudyHub() {
  const navigate = useNavigate();

  // Fetch health status
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: () => healthAPI.check(),
    retry: 3,
  });

  // Fetch statistics
  const { data: statsData } = useQuery({
    queryKey: ['stats'],
    queryFn: () => statsAPI.getStats(),
    refetchInterval: 30000, // Refresh every 30s
  });

  const studyTools = [
    {
      id: 'flashcards',
      title: 'Flashcards',
      description: 'Generate and review flashcards with spaced repetition (SM-2)',
      icon: Brain,
      color: 'from-purple-500 to-indigo-600',
      path: '/flashcards',
      stats: statsData ? `${statsData.flashcards.total} cards, ${statsData.flashcards.due} due` : 'Loading...',
    },
    {
      id: 'quiz',
      title: 'Quiz',
      description: 'Test your knowledge with AI-generated multiple choice questions',
      icon: Target,
      color: 'from-blue-500 to-cyan-600',
      path: '/quiz',
      stats: statsData ? `${statsData.by_type.quiz_attempt} attempts` : 'Loading...',
    },
    {
      id: 'match',
      title: 'Match Quiz',
      description: 'Match terms with definitions in this interactive game',
      icon: Zap,
      color: 'from-emerald-500 to-teal-600',
      path: '/match',
      stats: statsData ? `${statsData.by_type.match_attempt} attempts` : 'Loading...',
    },
    {
      id: 'upload',
      title: 'Upload Material',
      description: 'Upload PDFs or text to generate study materials',
      icon: FileText,
      color: 'from-amber-500 to-orange-600',
      path: '/upload',
      stats: 'Upload documents',
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="text-xl font-bold text-foreground">Notiq Study Hub</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                healthData?.status === 'healthy'
                  ? 'bg-green-500/20 text-green-700 dark:text-green-400'
                  : 'bg-red-500/20 text-red-700 dark:text-red-400'
              }`}>
                {healthData?.status === 'healthy' ? '● Connected' : '● Offline'}
              </div>
              <Button variant="ghost" size="icon">
                <Settings className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        {statsData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Total Interactions</CardDescription>
                <CardTitle className="text-3xl">{statsData.total_interactions}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center text-xs text-muted-foreground">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  All study activities
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Accuracy</CardDescription>
                <CardTitle className="text-3xl">{Math.round(statsData.overall_accuracy * 100)}%</CardTitle>
              </CardHeader>
              <CardContent>
                <Progress value={statsData.overall_accuracy * 100} className="h-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Due for Review</CardDescription>
                <CardTitle className="text-3xl">{statsData.flashcards.due}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center text-xs text-muted-foreground">
                  <Clock className="w-3 h-3 mr-1" />
                  Flashcards ready
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Verified Interactions</CardDescription>
                <CardTitle className="text-3xl">{statsData.verified_interactions}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center text-xs text-muted-foreground">
                  <BarChart3 className="w-3 h-3 mr-1" />
                  Quizzes & matches
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Study Tools */}
        <section>
          <h2 className="text-2xl font-bold mb-6">Study Tools</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {studyTools.map((tool) => {
              const Icon = tool.icon;
              return (
                <Card
                  key={tool.id}
                  className="cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => navigate(tool.path)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${tool.color} flex items-center justify-center`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <CardTitle className="mt-4">{tool.title}</CardTitle>
                    <CardDescription>{tool.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-sm text-muted-foreground">
                      {tool.stats}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </section>

        {/* Quick Actions */}
        <section className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle>Quick Start</CardTitle>
              <CardDescription>Jump into your most important tasks</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                onClick={() => navigate('/flashcards')}
                disabled={!statsData || statsData.flashcards.due === 0}
              >
                <Brain className="w-4 h-4 mr-2" />
                Review {statsData?.flashcards.due || 0} Due Cards
              </Button>
              <Button variant="outline" onClick={() => navigate('/upload')}>
                <FileText className="w-4 h-4 mr-2" />
                Upload New Material
              </Button>
              <Button variant="outline" onClick={() => navigate('/quiz')}>
                <Target className="w-4 h-4 mr-2" />
                Take a Quiz
              </Button>
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  );
}
