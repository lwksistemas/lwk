import Image from "next/image";
import { Bell, Mail } from "lucide-react";

interface DashboardHeaderProps {
  userName: string;
  userAvatar?: string;
}

export function DashboardHeader({ userName, userAvatar }: DashboardHeaderProps) {
  return (
    <header className="flex items-center justify-between mb-4 sm:mb-6">
      <div className="flex items-center gap-3 sm:gap-4">
        <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-purple-200 dark:bg-purple-900 flex items-center justify-center text-xl sm:text-2xl">
          💇‍♀️
        </div>
        <div>
          <h1 className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white">
            Bem-vindo, {userName}!
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
            Aqui está o resumo do salão hoje.
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3 sm:gap-6">
        <Bell className="w-5 h-5 sm:w-6 sm:h-6 text-gray-500 dark:text-gray-400 cursor-pointer hover:text-purple-600 transition-colors" />
        <Mail className="w-5 h-5 sm:w-6 sm:h-6 text-gray-500 dark:text-gray-400 cursor-pointer hover:text-purple-600 transition-colors hidden sm:block" />
        {userAvatar ? (
          <Image
            src={userAvatar}
            alt={userName}
            width={40}
            height={40}
            className="w-8 h-8 sm:w-10 sm:h-10 rounded-full object-cover"
            unoptimized
          />
        ) : (
          <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center text-white font-bold text-sm">
            {userName.charAt(0).toUpperCase()}
          </div>
        )}
      </div>
    </header>
  );
}
