import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Lightbulb, LogOut, Brain, Loader2 } from "lucide-react";
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
import { authService } from "@/lib/auth";
import { projectAPI, type Project } from "@/lib/api";
import { toast } from "sonner";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// Default icons for projects
const DEFAULT_ICONS = ["🎯", "📚", "🧬", "💻", "🎨", "🔬", "📊", "🏛️"];
const DEFAULT_COLORS = [
  "from-indigo-500 to-purple-600",
  "from-green-500 to-emerald-600",
  "from-blue-500 to-cyan-600",
  "from-orange-500 to-red-600",
  "from-pink-500 to-rose-600",
  "from-yellow-500 to-amber-600",
];

export default function Projects() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const user = authService.getCurrentUser();
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [selectedIcon, setSelectedIcon] = useState(DEFAULT_ICONS[0]);
  const [selectedColor, setSelectedColor] = useState(DEFAULT_COLORS[0]);

  // Fetch projects from backend
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectAPI.list(),
  });

  // Create project mutation
  const createProjectMutation = useMutation({
    mutationFn: (data: { name: string; icon: string; color: string }) =>
      projectAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowNewProject(false);
      setNewProjectName("");
      setSelectedIcon(DEFAULT_ICONS[0]);
      setSelectedColor(DEFAULT_COLORS[0]);
      toast.success("Project created successfully!");
    },
    onError: (error: Error) => {
      toast.error(`Failed to create project: ${error.message}`);
    },
  });

  const handleCreateProject = () => {
    if (!newProjectName.trim()) {
      toast.error("Please enter a project name");
      return;
    }

    createProjectMutation.mutate({
      name: newProjectName.trim(),
      icon: selectedIcon,
      color: selectedColor,
    });
  };

  const handleLogout = () => {
    authService.logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Top Bar with Logo and Logout */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
                <Brain className="w-6 h-6 text-primary-foreground" />
              </div>
              <span className="text-2xl font-bold">Notiq</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-lg">{user?.avatar || "👤"}</span>
                </div>
                <div>
                  <p className="text-sm font-medium">{user?.name}</p>
                  <p className="text-xs text-muted-foreground">{user?.email}</p>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-12">
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
            {isLoading && (
              <div className="col-span-full flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Loading projects...</span>
              </div>
            )}

            {!isLoading && projects.map((project) => (
              <Card
                key={project.id}
                className="cursor-pointer hover:shadow-lg transition-all group"
                onClick={() => navigate(`/project/${project.id}`)}
              >
                <CardHeader>
                  <div
                    className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${project.color || DEFAULT_COLORS[0]} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}
                  >
                    <span className="text-3xl">{project.icon || "📁"}</span>
                  </div>
                  <CardTitle className="text-xl">{project.name}</CardTitle>
                  <CardDescription>
                    {project.description || "No description"}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    size="sm"
                    variant="secondary"
                    className="w-full"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/project/${project.id}`);
                    }}
                  >
                    Open Project
                  </Button>
                </CardContent>
              </Card>
            ))}

            {/* Empty state if no projects */}
            {!isLoading && projects.length === 0 && (
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
      </main>

      {/* New Project Dialog */}
      <Dialog open={showNewProject} onOpenChange={setShowNewProject}>
        <DialogContent className="max-w-md">
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

            <div>
              <Label>Icon</Label>
              <div className="flex gap-2 mt-2 flex-wrap">
                {DEFAULT_ICONS.map((icon) => (
                  <button
                    key={icon}
                    type="button"
                    onClick={() => setSelectedIcon(icon)}
                    className={`w-12 h-12 rounded-lg flex items-center justify-center text-2xl transition-all ${
                      selectedIcon === icon
                        ? "bg-primary text-primary-foreground ring-2 ring-primary"
                        : "bg-secondary hover:bg-secondary/80"
                    }`}
                  >
                    {icon}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <Label>Color Theme</Label>
              <div className="flex gap-2 mt-2 flex-wrap">
                {DEFAULT_COLORS.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setSelectedColor(color)}
                    className={`w-12 h-12 rounded-lg bg-gradient-to-br ${color} transition-all ${
                      selectedColor === color ? "ring-2 ring-offset-2 ring-primary" : ""
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setShowNewProject(false)}
              disabled={createProjectMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateProject}
              disabled={!newProjectName.trim() || createProjectMutation.isPending}
            >
              {createProjectMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Project"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
