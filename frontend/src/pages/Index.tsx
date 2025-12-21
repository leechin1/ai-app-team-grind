import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, BookOpen, Calculator, Globe, Code, FlaskConical, BookText, Settings, LayoutGrid, List } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TemplateCard } from "@/components/TemplateCard";
import { NotebookCard } from "@/components/NotebookCard";
import { CreateNotebookDialog } from "@/components/CreateNotebookDialog";

const featuredTemplates = [
  {
    id: "bio-101",
    title: "Biology 101",
    subject: "Science",
    description: "Cell biology, genetics, and evolution fundamentals",
    sources: 12,
    gradient: "bg-gradient-to-br from-emerald-500 to-teal-600",
    icon: <FlaskConical className="w-4 h-4" />,
  },
  {
    id: "calculus",
    title: "Calculus Fundamentals",
    subject: "Mathematics",
    description: "Derivatives, integrals, and limits",
    sources: 8,
    gradient: "bg-gradient-to-br from-blue-500 to-indigo-600",
    icon: <Calculator className="w-4 h-4" />,
  },
  {
    id: "world-history",
    title: "World History",
    subject: "History",
    description: "Ancient civilizations to modern era",
    sources: 15,
    gradient: "bg-gradient-to-br from-amber-500 to-orange-600",
    icon: <Globe className="w-4 h-4" />,
  },
  {
    id: "programming",
    title: "Programming Basics",
    subject: "Computer Science",
    description: "Variables, loops, and functions",
    sources: 10,
    gradient: "bg-gradient-to-br from-violet-500 to-purple-600",
    icon: <Code className="w-4 h-4" />,
  },
  {
    id: "chemistry",
    title: "Chemistry Essentials",
    subject: "Science",
    description: "Atoms, molecules, and reactions",
    sources: 9,
    gradient: "bg-gradient-to-br from-cyan-500 to-blue-600",
    icon: <FlaskConical className="w-4 h-4" />,
  },
  {
    id: "literature",
    title: "Literature Analysis",
    subject: "English",
    description: "Literary devices and critical analysis",
    sources: 7,
    gradient: "bg-gradient-to-br from-rose-500 to-pink-600",
    icon: <BookText className="w-4 h-4" />,
  },
];

const recentNotebooks = [
  {
    id: "1",
    title: "Organic Chemistry Notes",
    notesCount: 24,
    lastEdited: "2 hours ago",
  },
  {
    id: "2",
    title: "Spanish Vocabulary",
    notesCount: 156,
    lastEdited: "Yesterday",
  },
  {
    id: "3",
    title: "Machine Learning Concepts",
    notesCount: 42,
    lastEdited: "3 days ago",
  },
];

export default function Index() {
  const navigate = useNavigate();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [filter, setFilter] = useState("all");

  const handleSelectTemplate = (templateId: string) => {
    navigate(`/dashboard?template=${templateId}`);
  };

  const handleSelectNotebook = (notebookId: string) => {
    navigate(`/dashboard?notebook=${notebookId}`);
  };

  const handleCreateNotebook = (title: string) => {
    const newId = Date.now().toString();
    navigate(`/dashboard?notebook=${newId}&title=${encodeURIComponent(title)}`);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold text-foreground">Notiq</span>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="default" onClick={() => navigate('/study')}>
                <BookOpen className="w-4 h-4 mr-2" />
                Study Hub
              </Button>
              <Button variant="ghost" size="icon">
                <Settings className="w-5 h-5" />
              </Button>
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <span className="text-sm font-medium text-primary">U</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <Tabs value={filter} onValueChange={setFilter}>
            <TabsList>
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="templates">Featured templates</TabsTrigger>
              <TabsTrigger value="recent">Recent</TabsTrigger>
            </TabsList>
          </Tabs>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className={viewMode === "grid" ? "bg-muted" : ""}
              onClick={() => setViewMode("grid")}
            >
              <LayoutGrid className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className={viewMode === "list" ? "bg-muted" : ""}
              onClick={() => setViewMode("list")}
            >
              <List className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Featured Templates */}
        {(filter === "all" || filter === "templates") && (
          <section className="mb-12">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-foreground">Featured templates</h2>
              <Button variant="ghost" size="sm" className="text-muted-foreground">
                See all
              </Button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {featuredTemplates.map((template) => (
                <TemplateCard
                  key={template.id}
                  {...template}
                  onClick={() => handleSelectTemplate(template.id)}
                />
              ))}
            </div>
          </section>
        )}

        {/* Recent Notebooks */}
        {(filter === "all" || filter === "recent") && (
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-foreground">Your notebooks</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {/* Create New Card */}
              <Card
                className="cursor-pointer border-2 border-dashed border-border hover:border-primary/50 transition-colors"
                onClick={() => setCreateDialogOpen(true)}
              >
                <CardContent className="p-4 flex flex-col items-center justify-center h-[140px] text-muted-foreground hover:text-primary transition-colors">
                  <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-2">
                    <Plus className="w-6 h-6" />
                  </div>
                  <span className="text-sm font-medium">Create new notebook</span>
                </CardContent>
              </Card>

              {/* Recent Notebooks */}
              {recentNotebooks.map((notebook) => (
                <NotebookCard
                  key={notebook.id}
                  {...notebook}
                  onClick={() => handleSelectNotebook(notebook.id)}
                />
              ))}
            </div>
          </section>
        )}
      </main>

      {/* Create Dialog */}
      <CreateNotebookDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSubmit={handleCreateNotebook}
      />
    </div>
  );
}
