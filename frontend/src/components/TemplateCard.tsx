import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface TemplateCardProps {
  title: string;
  subject: string;
  description: string;
  sources: number;
  gradient: string;
  icon: React.ReactNode;
  onClick: () => void;
}

export function TemplateCard({
  title,
  subject,
  description,
  sources,
  gradient,
  icon,
  onClick,
}: TemplateCardProps) {
  return (
    <Card
      className={cn(
        "group cursor-pointer overflow-hidden border-0 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg",
        gradient
      )}
      onClick={onClick}
    >
      <CardContent className="p-0">
        <div className="relative h-32 p-4 flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <span className="text-xs font-medium text-white/80 bg-white/20 px-2 py-0.5 rounded-full backdrop-blur-sm">
              {subject}
            </span>
            <div className="w-8 h-8 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center text-white">
              {icon}
            </div>
          </div>
          <div>
            <h3 className="font-semibold text-white text-lg leading-tight">{title}</h3>
            <p className="text-white/70 text-xs mt-1 line-clamp-1">{description}</p>
          </div>
        </div>
        <div className="bg-card px-4 py-3 border-t border-border">
          <span className="text-xs text-muted-foreground">{sources} sources</span>
        </div>
      </CardContent>
    </Card>
  );
}
