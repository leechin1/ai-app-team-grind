import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Clock } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import ProjectLayout from "@/components/ProjectLayout";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import "@/styles/quill-custom.css";

// Mock data for MVP
const MOCK_NOTES: Record<string, { title: string; course: string; dueDate: string; type: string; content: string }> = {
  "1": {
    title: "Introduction to Biology",
    course: "Biology 101",
    dueDate: "2025-12-30",
    type: "Study Notes",
    content: "<h2>Cell Biology</h2><p>Cells are the basic unit of life...</p><h3>Mitochondria</h3><p>The powerhouse of the cell...</p>"
  },
  "2": {
    title: "React Programming",
    course: "Web Development",
    dueDate: "2025-12-28",
    type: "Project Notes",
    content: "<h2>React Hooks</h2><p>Hooks let you use state and other React features...</p><h3>useState</h3><p>The useState hook...</p>"
  },
  "3": {
    title: "Organic Chemistry Notes",
    course: "Chemistry 201",
    dueDate: "2026-01-05",
    type: "Lecture Notes",
    content: "<h2>Chemical Bonds</h2><p>Atoms form bonds through...</p><h3>Covalent Bonds</h3><p>Electrons are shared...</p>"
  },
};

const modules = {
  toolbar: [
    [{ header: [1, 2, 3, false] }],
    ["bold", "italic", "underline", "strike"],
    [{ list: "ordered" }, { list: "bullet" }],
    ["blockquote", "code-block"],
    [{ color: [] }, { background: [] }],
    ["link", "image"],
    ["clean"],
  ],
};

export default function Editor() {
  const { projectId } = useParams<{ projectId: string }>();
  const [title, setTitle] = useState("");
  const [course, setCourse] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [type, setType] = useState("");
  const [content, setContent] = useState("");
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  useEffect(() => {
    // Load note from mock data
    if (projectId && MOCK_NOTES[projectId]) {
      const note = MOCK_NOTES[projectId];
      setTitle(note.title);
      setCourse(note.course);
      setDueDate(note.dueDate);
      setType(note.type);
      setContent(note.content);
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
  }, [title, course, dueDate, type, content]);

  return (
    <ProjectLayout>
      <div className="h-full flex flex-col">
        {/* Top Bar */}
        <div className="border-b px-8 py-4 flex items-center justify-between bg-white">
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
        <div className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-50 to-gray-100">
          <div className="max-w-4xl mx-auto px-8 py-12">
            <div className="bg-white rounded-lg shadow-sm p-8">
              {/* Title Input */}
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Untitled"
                className="text-4xl font-bold border-none px-0 mb-8 focus-visible:ring-0 focus-visible:ring-offset-0"
              />

              {/* Template Fields */}
              <div className="grid grid-cols-3 gap-4 mb-8 pb-8 border-b">
                <div className="space-y-2">
                  <Label htmlFor="course" className="text-sm font-medium text-muted-foreground">
                    Course
                  </Label>
                  <Input
                    id="course"
                    value={course}
                    onChange={(e) => setCourse(e.target.value)}
                    placeholder="e.g., Biology 101"
                    className="text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dueDate" className="text-sm font-medium text-muted-foreground">
                    Due Date
                  </Label>
                  <Input
                    id="dueDate"
                    type="date"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="type" className="text-sm font-medium text-muted-foreground">
                    Type
                  </Label>
                  <Input
                    id="type"
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                    placeholder="e.g., Study Notes"
                    className="text-sm"
                  />
                </div>
              </div>

              {/* Quill Editor */}
              <div className="quill-container">
                <ReactQuill
                  theme="snow"
                  value={content}
                  onChange={setContent}
                  modules={modules}
                  placeholder="Start writing your notes..."
                  className="min-h-[500px]"
                />
              </div>

              {/* Helper Text */}
              <div className="mt-8 pt-8 border-t text-sm text-muted-foreground space-y-2">
                <p>💡 <strong>Tip:</strong> Use ChatIQ to ask questions about your notes</p>
                <p>🧠 <strong>Tip:</strong> Generate flashcards and quizzes from your content</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProjectLayout>
  );
}
