import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { Brain, Sparkles, BookOpen, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { authService } from "@/lib/auth";

export default function Login() {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect if already logged in
    if (authService.isAuthenticated()) {
      navigate("/home");
    }
  }, [navigate]);

  const handleLogin = () => {
    authService.login();
    navigate("/home");
  };

  const handleGuestLogin = () => {
    authService.loginAsGuest();
    navigate("/home");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-3 mb-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg">
              <Brain className="w-9 h-9 text-white" />
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
              Notiq
            </h1>
          </div>
          <p className="text-2xl text-muted-foreground mb-4">
            Your AI-Powered Study Workspace
          </p>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Write, learn, and master your subjects with intelligent flashcards, quizzes, and an AI assistant that understands your notes.
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-12">
          <Card className="p-6 text-center hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center mx-auto mb-4">
              <BookOpen className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="font-semibold mb-2">Smart Note Editor</h3>
            <p className="text-sm text-muted-foreground">
              Notion-style editor with AI assistance
            </p>
          </Card>

          <Card className="p-6 text-center hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center mx-auto mb-4">
              <Brain className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="font-semibold mb-2">AI Study Tools</h3>
            <p className="text-sm text-muted-foreground">
              Auto-generate flashcards and quizzes
            </p>
          </Card>

          <Card className="p-6 text-center hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-6 h-6 text-emerald-600" />
            </div>
            <h3 className="font-semibold mb-2">ChatIQ Assistant</h3>
            <p className="text-sm text-muted-foreground">
              Context-aware AI chatbot for your projects
            </p>
          </Card>
        </div>

        {/* Auth Buttons */}
        <Card className="max-w-md mx-auto p-8">
          <h2 className="text-2xl font-bold text-center mb-6">Get Started</h2>
          <div className="space-y-4">
            <Button
              size="lg"
              className="w-full gap-2"
              onClick={handleLogin}
            >
              <Brain className="w-5 h-5" />
              Login as Demo User
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="w-full gap-2"
              onClick={handleGuestLogin}
            >
              <Zap className="w-5 h-5" />
              Continue as Guest
            </Button>
          </div>
          <p className="text-xs text-center text-muted-foreground mt-6">
            MVP Mode: Fake authentication for demonstration purposes
          </p>
        </Card>

        {/* Footer */}
        <p className="text-center text-sm text-muted-foreground mt-12">
          Built with Gemini AI • SM-2 Spaced Repetition • RAG-Ready
        </p>
      </div>
    </div>
  );
}
