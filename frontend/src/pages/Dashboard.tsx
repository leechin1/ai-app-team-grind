import { useState, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import {
  Plus, Upload, FileText, Search, MessageSquare,
  BookOpen, Sparkles, BarChart3, Brain,
  FileStack, Presentation, Settings,
  ChevronLeft, MoreVertical, Send, Loader2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';
import '@uiw/react-markdown-preview/markdown.css';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { structureNote, chatWithAI, uploadFile } from "@/lib/api";
import { toast } from "sonner";

interface Source {
  id: string;
  title: string;
  type: "note" | "pdf" | "web";
  createdAt: string;
  content?: string;
  structured?: string;
  file_uri?: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const studioTools = [
  { id: "flashcards", icon: Brain, label: "Flashcards", description: "Generate study flashcards" },
  { id: "quiz", icon: BarChart3, label: "Quiz", description: "Create practice quizzes" },
  { id: "report", icon: FileStack, label: "Reports", description: "Generate summary reports" },
  { id: "infographic", icon: Sparkles, label: "Infographic", description: "Visual content summary" },
  { id: "slides", icon: Presentation, label: "Slide Deck", description: "Create presentation slides" },
];

export default function Dashboard() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const notebookTitle = searchParams.get("title") || "Untitled notebook";

  const [sources, setSources] = useState<Source[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Note Creation State
  const [isNoteDialogOpen, setIsNoteDialogOpen] = useState(false);
  const [noteTitle, setNoteTitle] = useState("");
  const [noteContent, setNoteContent] = useState("");
  const [isStructuring, setIsStructuring] = useState(false);
  const [activeSourceId, setActiveSourceId] = useState<string | null>(null);

  // File Upload Handler
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      toast.error("Only PDF files are supported currently.");
      return;
    }

    const toastId = toast.loading("Uploading and processing PDF...");

    try {
      const result = await uploadFile(file);

      const newNoteId = Date.now().toString();
      const newSource: Source = {
        id: newNoteId,
        title: result.filename,
        type: "pdf",
        createdAt: new Date().toISOString(),
        file_uri: result.filename,
        content: result.preview || "PDF Document uploaded. You can now chat with it.",
        structured: ""
      };

      setSources(prev => [...prev, newSource]);
      setActiveSourceId(newNoteId);

      // Auto-initiate chat
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: "assistant",
        content: `I've uploaded "${result.filename}". You can now ask questions about it or ask me to structure a note from it.`
      }]);

      toast.success("PDF uploaded successfully", { id: toastId });
    } catch (error) {
      console.error(error);
      toast.error("Failed to upload PDF", { id: toastId });
    } finally {
      // Reset input
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleCreateNote = async () => {
    if (!noteTitle.trim() || !noteContent.trim()) {
      toast.error("Please provide both title and content");
      return;
    }

    setIsStructuring(true);
    const newNoteId = Date.now().toString();

    try {
      // 1. Create source immediately (optimistic UI)
      const newSource: Source = {
        id: newNoteId,
        title: noteTitle,
        type: "note",
        createdAt: new Date().toISOString(),
        content: noteContent,
      };
      setSources(prev => [...prev, newSource]);
      setActiveSourceId(newNoteId);
      setIsNoteDialogOpen(false);

      toast.info("Structuring note with AI...");

      // 2. Call API to structure
      const result = await structureNote(newNoteId, noteContent);

      // 3. Update source with structured content
      setSources(prev => prev.map(s =>
        s.id === newNoteId ? { ...s, structured: result.structured } : s
      ));

      toast.success("Note structured successfully!");

      // 4. Add initial AI message
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: "assistant",
        content: `I've structured your note "${noteTitle}". You can now see the organized version in the Studio panel.`
      }]);

    } catch (error) {
      console.error(error);
      toast.error("Failed to structure note");
    } finally {
      setIsStructuring(false);
      setNoteTitle("");
      setNoteContent("");
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputValue,
    };
    setMessages([...messages, userMessage]);
    setInputValue("");
    setIsChatLoading(true);

    // Call API
    try {
      const currentContent = activeSource ? activeSource.structured || activeSource.content : undefined;
      const response = await chatWithAI(inputValue, currentContent, activeSourceId || undefined, activeSource?.file_uri);

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error(error);
      toast.error("Failed to get AI response");
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleToolClick = (toolId: string) => {
    console.log("Tool clicked:", toolId);
    toast.info(`Generating ${toolId}... (Coming soon)`);
  };

  const activeSource = sources.find(s => s.id === activeSourceId);

  return (
    <div className="h-screen w-screen bg-background flex flex-col overflow-hidden">
      {/* Header */}
      <header className="h-14 border-b border-border bg-card/50 backdrop-blur-sm flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
            <ChevronLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-semibold text-foreground">{decodeURIComponent(notebookTitle)}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" className="gap-2" onClick={() => setIsNoteDialogOpen(true)}>
            <Plus className="w-4 h-4" />
            Add Note
          </Button>
          <Button variant="outline" size="sm">Share</Button>
          <Button variant="ghost" size="icon">
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </header>

      {/* Main Content - 3 Panel Layout */}
      <div className="flex-1 flex overflow-hidden w-full">
        <ResizablePanelGroup direction="horizontal" className="w-full">

          {/* Left Panel - Sources */}
          <ResizablePanel defaultSize={20} minSize={15} maxSize={30}>
            <div className="h-full border-r border-border bg-card/30 flex flex-col">
              <div className="p-3 border-b border-border">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="font-semibold text-foreground">Sources</h2>
                  <Button variant="ghost" size="icon" className="h-7 w-7">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </div>

                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  accept=".pdf"
                  onChange={handleFileUpload}
                />

                <Button
                  variant="outline"
                  className="w-full justify-center gap-2"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="w-4 h-4" />
                  Add sources (PDF)
                </Button>
              </div>

              {/* Deep Research CTA */}
              <div className="p-3">
                <div className="bg-gradient-to-r from-violet-600/20 to-purple-600/20 border border-violet-500/30 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-sm">
                    <Sparkles className="w-4 h-4 text-violet-400" />
                    <span className="text-violet-300 font-medium">Try Deep Research</span>
                    <span className="text-muted-foreground text-xs">for in-depth report</span>
                  </div>
                </div>
              </div>

              {/* Search */}
              <div className="px-3 pb-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search the web for new sources"
                    className="pl-9 bg-muted/50"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>

              {/* Sources List */}
              <ScrollArea className="flex-1 px-3">
                {sources.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <FileText className="w-10 h-10 text-muted-foreground/50 mb-3" />
                    <p className="text-sm text-muted-foreground font-medium">Saved sources will appear here</p>
                    <p className="text-xs text-muted-foreground/70 mt-1 max-w-[200px]">
                      Click Add source above to add PDFs, websites, text, or audio files.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {sources.map((source) => (
                      <Card
                        key={source.id}
                        className={`cursor-pointer transition-colors ${activeSourceId === source.id ? 'bg-muted border-primary/50' : 'hover:bg-muted/50'}`}
                        onClick={() => setActiveSourceId(source.id)}
                      >
                        <CardContent className="p-3 flex items-center gap-3">
                          <FileText className="w-4 h-4 text-muted-foreground" />
                          <div className="flex-1 min-w-0">
                            <span className="text-sm font-medium truncate block">{source.title}</span>
                            <span className="text-xs text-muted-foreground">{new Date(source.createdAt).toLocaleDateString()}</span>
                          </div>
                          {source.structured && <Sparkles className="w-3 h-3 text-violet-400" />}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </div>
          </ResizablePanel>

          <ResizableHandle />

          {/* Center Panel - Chat */}
          <ResizablePanel defaultSize={40} minSize={30}>
            <div className="h-full flex flex-col min-w-0">
              <div className="p-3 border-b border-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h2 className="font-semibold text-foreground">Chat</h2>
                  <MessageSquare className="w-4 h-4 text-muted-foreground" />
                </div>
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="icon" className="h-7 w-7">
                    <Settings className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Chat Messages */}
              <ScrollArea className="flex-1 p-4">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <Upload className="w-12 h-12 text-muted-foreground/50 mb-4" />
                    <h3 className="text-lg font-medium text-foreground mb-2">Add a source to get started</h3>
                    <Button variant="outline" onClick={() => setIsNoteDialogOpen(true)}>
                      Upload a source
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${message.role === "user"
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted text-foreground"
                            }`}
                        >
                          <p className="text-sm">{message.content}</p>
                        </div>
                      </div>
                    ))}
                    {isChatLoading && (
                      <div className="flex justify-start">
                        <div className="bg-muted rounded-2xl px-4 py-2.5">
                          <div className="flex gap-1">
                            <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-pulse" />
                            <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-pulse delay-100" />
                            <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-pulse delay-200" />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </ScrollArea>

              {/* Chat Input */}
              <div className="p-4 border-t border-border">
                <div className="relative">
                  <Textarea
                    placeholder="Ask about your sources..."
                    className="min-h-[44px] max-h-32 pr-12 resize-none bg-muted/50"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                  />
                  <Button
                    size="icon"
                    className="absolute right-2 bottom-2 h-8 w-8"
                    onClick={handleSendMessage}
                    disabled={!inputValue.trim() || isChatLoading}
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground text-center mt-2">
                  {sources.length} sources
                </p>
              </div>
            </div>
          </ResizablePanel>

          <ResizableHandle />

          {/* Right Panel - Studio */}
          <ResizablePanel defaultSize={40} minSize={30}>
            <div className="h-full border-l border-border bg-card/30 flex flex-col">
              <div className="p-3 border-b border-border flex items-center justify-between">
                <h2 className="font-semibold text-foreground">Studio</h2>
                <Button variant="ghost" size="icon" className="h-7 w-7">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </div>

              <ResizablePanelGroup direction="vertical">
                <ResizablePanel defaultSize={25} minSize={15} maxSize={40}>
                  <ScrollArea className="h-full">
                    <div className="p-4">
                      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                        Generate Content
                      </h3>
                      <div className="space-y-2">
                        {studioTools.map((tool) => (
                          <Button
                            key={tool.id}
                            variant="ghost"
                            className="w-full justify-start gap-3 h-auto py-3 px-3 hover:bg-primary/10 hover:text-primary transition-colors group"
                            onClick={() => handleToolClick(tool.id)}
                          >
                            <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                              <tool.icon className="w-4 h-4" />
                            </div>
                            <div className="flex-1 text-left">
                              <div className="text-sm font-medium">{tool.label}</div>
                              <div className="text-xs text-muted-foreground group-hover:text-primary/70">
                                {tool.description}
                              </div>
                            </div>
                          </Button>
                        ))}
                      </div>
                    </div>
                  </ScrollArea>
                </ResizablePanel>

                <ResizableHandle withHandle />

                <ResizablePanel defaultSize={75}>
                  <div className="h-full flex flex-col overflow-hidden">
                    {activeSource ? (
                      <div className="flex-1 overflow-auto" data-color-mode="light">
                        <MDEditor
                          value={activeSource.structured || activeSource.content || ""}
                          onChange={(value) => {
                            setSources(prev => prev.map(s =>
                              s.id === activeSourceId ? { ...s, structured: value || "" } : s
                            ));
                          }}
                          height="100%"
                          preview="edit"
                          hideToolbar={false}
                          enableScroll={true}
                          visibleDragbar={false}
                          className="border-0"
                        />
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center flex-1 h-full text-center p-4">
                        <Sparkles className="w-10 h-10 text-muted-foreground/50 mb-3" />
                        <p className="text-sm text-muted-foreground font-medium">Studio is ready.</p>
                        <p className="text-xs text-muted-foreground/70 mt-1 max-w-[180px]">
                          Select a note to start editing or ask AI to generate content.
                        </p>
                      </div>
                    )}
                  </div>
                </ResizablePanel>
              </ResizablePanelGroup>

              {/* Add Note Button */}
              <div className="p-1 border-t border-border flex justify-center">
                <Button variant="ghost" size="sm" className="h-6 gap-2 text-[10px] text-muted-foreground hover:text-foreground" onClick={() => setIsNoteDialogOpen(true)}>
                  <Plus className="w-3 h-3" />
                  Add note
                </Button>
              </div>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>

      {/* Note Creation Dialog */}
      <Dialog open={isNoteDialogOpen} onOpenChange={setIsNoteDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Add New Note</DialogTitle>
            <DialogDescription>
              Write your notes or upload a PDF. AI will structure and organize them for you.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Input
                id="title"
                placeholder="Note Title"
                value={noteTitle}
                onChange={(e) => setNoteTitle(e.target.value)}
              />
            </div>

            {/* PDF Upload Option */}
            <div className="flex items-center gap-2">
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".pdf"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;

                  try {
                    const result = await uploadFile(file);
                    setNoteTitle(result.filename);
                    setNoteContent(result.content || result.preview);
                    toast.success("PDF content loaded");
                  } catch (error) {
                    console.error(error);
                    toast.error("Failed to load PDF");
                  }
                }}
              />
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-4 h-4 mr-2" />
                Upload PDF
              </Button>
            </div>

            {/* Markdown Editor */}
            <div className="border rounded-md overflow-hidden" data-color-mode="light">
              <MDEditor
                value={noteContent}
                onChange={(value) => setNoteContent(value || "")}
                height={300}
                preview="edit"
                hideToolbar={false}
                visibleDragbar={false}
              />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleCreateNote} disabled={isStructuring}>
              {isStructuring ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Structuring...
                </>
              ) : (
                "Create & Structure"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
