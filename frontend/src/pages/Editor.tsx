import { useState, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { Clock, Save } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import ProjectLayout from "@/components/ProjectLayout";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import "@/styles/quill-custom.css";
import { noteAPI } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

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
  const { projectId, noteId } = useParams<{ projectId: string; noteId?: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [title, setTitle] = useState("");
  const [course, setCourse] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [type, setType] = useState("Study Notes");
  const [content, setContent] = useState("");
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Load existing note if noteId is provided
  const { data: existingNote, isLoading } = useQuery({
    queryKey: ['note', noteId],
    queryFn: () => {
      if (!noteId) throw new Error("No note ID");
      return noteAPI.getById(noteId);
    },
    enabled: !!noteId,
  });

  // Initialize form with existing note data
  useEffect(() => {
    if (existingNote) {
      setTitle(existingNote.title);
      setCourse(existingNote.course || "");
      setDueDate(existingNote.due_date || "");
      setType(existingNote.type || "Study Notes");
      setContent(existingNote.content_html || existingNote.content || "");
      setLastSaved(new Date(existingNote.updated_at));
      setHasUnsavedChanges(false);
    }
  }, [existingNote]);

  // Track changes
  useEffect(() => {
    if (existingNote && (
      title !== existingNote.title ||
      course !== (existingNote.course || "") ||
      dueDate !== (existingNote.due_date || "") ||
      type !== (existingNote.type || "Study Notes") ||
      content !== (existingNote.content_html || existingNote.content || "")
    )) {
      setHasUnsavedChanges(true);
    }
  }, [title, course, dueDate, type, content, existingNote]);

  // Create note mutation
  const createMutation = useMutation({
    mutationFn: () => {
      if (!projectId) throw new Error("No project ID");
      return noteAPI.create({
        project_id: projectId,
        title: title || "Untitled",
        content: content,
        content_html: content,
        course: course || undefined,
        due_date: dueDate || undefined,
        type: type || "Study Notes",
      });
    },
    onSuccess: (data) => {
      toast.success('Note created successfully!');
      setLastSaved(new Date());
      setHasUnsavedChanges(false);
      queryClient.invalidateQueries({ queryKey: ['notes', projectId] });
      // Navigate to edit mode with the new note ID
      navigate(`/project/${projectId}/editor/${data.id}`, { replace: true });
    },
    onError: (error: Error) => {
      toast.error(`Failed to create note: ${error.message}`);
    },
  });

  // Update note mutation
  const updateMutation = useMutation({
    mutationFn: () => {
      if (!noteId) throw new Error("No note ID");
      return noteAPI.update(noteId, {
        title: title || "Untitled",
        content: content,
        content_html: content,
        course: course || undefined,
        due_date: dueDate || undefined,
        type: type || undefined,
      });
    },
    onSuccess: () => {
      toast.success('Note saved successfully!');
      setLastSaved(new Date());
      setHasUnsavedChanges(false);
      queryClient.invalidateQueries({ queryKey: ['note', noteId] });
      queryClient.invalidateQueries({ queryKey: ['notes', projectId] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to save note: ${error.message}`);
    },
  });

  const handleSave = () => {
    if (noteId) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
  };

  const isSaving = createMutation.isPending || updateMutation.isPending;

  if (isLoading && noteId) {
    return (
      <ProjectLayout>
        <div className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">Loading note...</p>
        </div>
      </ProjectLayout>
    );
  }

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
            {hasUnsavedChanges && !lastSaved && (
              <span className="text-amber-600">Unsaved changes</span>
            )}
          </div>
          <Button
            onClick={handleSave}
            disabled={isSaving || (!hasUnsavedChanges && !!noteId)}
            size="sm"
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? 'Saving...' : noteId ? 'Save Changes' : 'Create Note'}
          </Button>
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
            </div>
          </div>
        </div>
      </div>
    </ProjectLayout>
  );
}
