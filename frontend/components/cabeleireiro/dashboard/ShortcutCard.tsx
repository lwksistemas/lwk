import { LucideIcon } from "lucide-react";

interface ShortcutCardProps {
  title: string;
  icon: LucideIcon;
  onClick: () => void;
}

export function ShortcutCard({ title, icon: Icon, onClick }: ShortcutCardProps) {
  return (
    <div 
      onClick={onClick}
      className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 flex items-center gap-4 cursor-pointer hover:shadow-md transition-all hover:scale-105"
    >
      <div className="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
        <Icon className="text-purple-600 dark:text-purple-400" />
      </div>
      <p className="font-medium text-gray-900 dark:text-white">{title}</p>
    </div>
  );
}
