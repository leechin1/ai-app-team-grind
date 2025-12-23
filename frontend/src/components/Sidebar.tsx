import { useNavigate, useLocation } from "react-router-dom";
import { Home, MessageCircle, Brain, Zap, Target, FolderOpen, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { authService } from "@/lib/auth";
import { cn } from "@/lib/utils";

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authService.getCurrentUser();

  const navigation = [
    { name: "Home", icon: Home, path: "/home" },
    { name: "ChatIQ", icon: MessageCircle, path: "/chatiq" },
    { name: "Flashcards", icon: Brain, path: "/flashcards" },
    { name: "Match Quiz", icon: Zap, path: "/match" },
    { name: "Quiz", icon: Target, path: "/quiz" },
    { name: "Files", icon: FolderOpen, path: "/files" },
  ];

  const handleLogout = () => {
    authService.logout();
    navigate("/");
  };

  return (
    <div className="flex h-screen w-64 flex-col border-r bg-card">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <Brain className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold">Notiq</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Button
              key={item.name}
              variant={isActive ? "secondary" : "ghost"}
              className={cn(
                "w-full justify-start gap-3",
                isActive && "bg-secondary font-semibold"
              )}
              onClick={() => navigate(item.path)}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </Button>
          );
        })}
      </nav>

      {/* User Info & Logout */}
      <div className="border-t p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
            <span className="text-lg">{user?.avatar || "👤"}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.name}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="w-full gap-2"
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4" />
          Logout
        </Button>
      </div>
    </div>
  );
}
