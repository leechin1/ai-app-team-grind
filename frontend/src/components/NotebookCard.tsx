import { Card, CardContent } from "@/components/ui/card";
import { FileText, MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface NotebookCardProps {
  id: string;
  title: string;
  notesCount: number;
  lastEdited: string;
  onClick: () => void;
}

export function NotebookCard({
  title,
  notesCount,
  lastEdited,
  onClick,
}: NotebookCardProps) {
  return (
    <Card
      className="group cursor-pointer border border-border bg-card transition-all duration-200 hover:border-primary/50 hover:shadow-md"
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <FileText className="w-5 h-5 text-primary" />
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>Rename</DropdownMenuItem>
              <DropdownMenuItem>Duplicate</DropdownMenuItem>
              <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <h3 className="font-medium text-foreground mb-1 line-clamp-1">{title}</h3>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{notesCount} notes</span>
          <span>•</span>
          <span>{lastEdited}</span>
        </div>
      </CardContent>
    </Card>
  );
}
