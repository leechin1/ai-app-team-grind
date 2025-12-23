import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, BookOpen, Code, Beaker, Globe, Book, Lightbulb } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Sidebar from "@/components/Sidebar";

// Mock projects for MVP
const MOCK_PROJECTS = [
  { id: "1", name: "Biology", icon: "🧬", color: "from-green-500 to-emerald-600", noteCount: 5 },
  { id: "2", name: "Programming", icon: "💻", color: "from-blue-500 to-cyan-600", noteCount: 12 },
  { id: "3", name: "Chemistry", icon: "🧪", color: "from-purple-500 to-pink-600", noteCount: 8 },
  { id: "4", name: "History", icon: "📚", color: "from-amber-500 to-orange-600", noteCount: 3 },
];

export default function Projects() {
  const navigate = useNavigate();
  const [projects] = useState(MOCK_PROJECTS);
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");

  const handleCreateProject = () => {
    // TODO: Call backend to create project
    console.log("Creating project:", newProjectName);
    setShowNewProject(false);
    setNewProjectName("");
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-8 py-12">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold mb-2">Projects</h1>
              <p className="text-muted-foreground">
                Organize your learning by subject or topic
              </p>
            </div>
            <Button size="lg" onClick={() => setShowNewProject(true)}>
              <Plus className="w-5 h-5 mr-2" />
              New Project
            </Button>
          </div>

          {/* Projects Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {projects.map((project) => (
              <Card
                key={project.id}
                className="cursor-pointer hover:shadow-lg transition-all group"
                onClick={() => navigate(`/editor/${project.id}`)}
              >
                <CardHeader>
                  <div
                    className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${project.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}
                  >
                    <span className="text-3xl">{project.icon}</span>
                  </div>
                  <CardTitle className="text-xl">{project.name}</CardTitle>
                  <CardDescription>
                    {project.noteCount} note{project.noteCount !== 1 ? "s" : ""}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="flex-1"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/editor/${project.id}`);
                      }}
                    >
                      Open
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/chatiq?project=${project.id}`);
                      }}
                    >
                      Chat
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}

            {/* Empty state if no projects */}
            {projects.length === 0 && (
              <Card className="col-span-full p-12 text-center">
                <Lightbulb className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-xl font-semibold mb-2">No projects yet</h3>
                <p className="text-muted-foreground mb-6">
                  Create your first project to start organizing your notes
                </p>
                <Button onClick={() => setShowNewProject(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Project
                </Button>
              </Card>
            )}
          </div>
        </div>
      </main>

      {/* New Project Dialog */}
      <Dialog open={showNewProject} onOpenChange={setShowNewProject}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
            <DialogDescription>
              Organize your notes and study materials by subject or topic
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="name">Project Name</Label>
              <Input
                id="name"
                placeholder="e.g., Biology, Programming, History"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && newProjectName.trim()) {
                    handleCreateProject();
                  }
                }}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowNewProject(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateProject}
              disabled={!newProjectName.trim()}
            >
              Create Project
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
