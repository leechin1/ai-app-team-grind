import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Save, Clock } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import Sidebar from "@/components/Sidebar";

// Mock data for MVP
const MOCK_NOTES: Record<string, { title: string; content: string }> = {
  "1": {
    title: "Introduction to Biology",
    content: "# Cell Biology\n\nCells are the basic unit of life...\n\n## Mitochondria\nThe powerhouse of the cell..."
  },
  "2": {
    title: "React Programming",
    content: "# React Hooks\n\nHooks let you use state and other React features...\n\n## useState\nThe useState hook..."
  },
  "3": {
    title: "Organic Chemistry Notes",
    content: "# Chemical Bonds\n\nAtoms form bonds through...\n\n## Covalent Bonds\nElectrons are shared..."
  },
};

export default function Editor() {
  const { projectId } = useParams<{ projectId: string }>();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  useEffect(() => {
    // Load note from mock data
    if (projectId && MOCK_NOTES[projectId]) {
      setTitle(MOCK_NOTES[projectId].title);
      setContent(MOCK_NOTES[projectId].content);
    }
  }, [projectId]);

  // Auto-save simulation
  useEffect(() => {
    const timer = setTimeout(() => {
      if (title || content) {
        setLastSaved(new Date());
        // TODO: Call backend to save
      }
    }, 2000);

    return () => clearTimeout(timer);
  }, [title, content]);

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <main className="flex-1 overflow-hidden">
        <div className="h-full flex flex-col">
          {/* Top Bar */}
          <div className="border-b px-8 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              {lastSaved && (
                <>
                  <Clock className="w-4 h-4" />
                  <span>Last saved {lastSaved.toLocaleTimeString()}</span>
                </>
              )}
            </div>
          </div>

          {/* Editor Container - Centered, 40-50% width */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-3xl mx-auto px-8 py-12">
              {/* Title Input */}
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Untitled"
                className="text-4xl font-bold border-none px-0 mb-6 focus-visible:ring-0 focus-visible:ring-offset-0"
              />

              {/* Content Editor */}
              <Textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Start writing... Use Markdown for formatting"
                className="min-h-[600px] text-lg leading-relaxed border-none px-0 resize-none focus-visible:ring-0 focus-visible:ring-offset-0"
              />

              {/* Helper Text */}
              <div className="mt-8 text-sm text-muted-foreground space-y-2">
                <p>💡 <strong>Tip:</strong> Use ChatIQ to ask questions about your notes</p>
                <p>🧠 <strong>Tip:</strong> Generate flashcards and quizzes from your content</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
