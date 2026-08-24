'use client';

import Link from 'next/link';
import { BookOpen, ChevronDown, CircleHelp, FileText, KeyRound, LogOut, Moon, Settings, Sun, UserRound } from 'lucide-react';

type ClinicaGeralUserMenuProps = {
  base: string;
  slug: string;
  lojaNome: string;
  usuario: { nome: string; email: string };
  aberto: boolean;
  darkMode: boolean;
  onToggle: () => void;
  onClose: () => void;
  onLogout: () => void;
  onToggleTheme: () => void;
};

export function ClinicaGeralUserMenu({
  base,
  slug,
  lojaNome,
  usuario,
  aberto,
  darkMode,
  onToggle,
  onClose,
  onLogout,
  onToggleTheme,
}: ClinicaGeralUserMenuProps) {
  return (
    <div className="relative">
      <button
        type="button"
        onClick={onToggle}
        className="flex items-center gap-1 rounded p-1.5 hover:bg-white/10"
        aria-label="Menu do usuário"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/20 text-xs">
          {lojaNome.slice(0, 1).toUpperCase()}
        </span>
        <ChevronDown className="h-3.5 w-3.5" />
      </button>
      {aberto && (
        <div className="absolute right-0 mt-1 w-72 overflow-hidden rounded-md border border-slate-200 bg-white text-slate-800 shadow-lg dark:border-white/10 dark:bg-[#1E1D3A] dark:text-slate-100">
          <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3 dark:border-white/10">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-sm font-medium text-slate-600 dark:bg-white/10 dark:text-slate-200">
              {(usuario.nome || lojaNome).slice(0, 1).toUpperCase()}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{usuario.nome || lojaNome}</p>
              {usuario.email ? <p className="truncate text-xs text-slate-500 dark:text-slate-400">{usuario.email}</p> : null}
            </div>
          </div>
          <div className="py-1">
            <Link href={`${base}/perfil`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-white/5">
              <UserRound className="h-4 w-4 text-slate-500 dark:text-slate-400" />
              Meu perfil
            </Link>
            <Link href={`${base}/configuracoes`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-white/5">
              <Settings className="h-4 w-4 text-slate-500 dark:text-slate-400" />
              Configurações
            </Link>
            <button
              type="button"
              onClick={() => {
                onToggleTheme();
                onClose();
              }}
              className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-white/5"
            >
              {darkMode ? <Sun className="h-4 w-4 text-slate-500 dark:text-slate-400" /> : <Moon className="h-4 w-4 text-slate-500 dark:text-slate-400" />}
              {darkMode ? 'Modo claro' : 'Modo escuro'}
            </button>
            <Link href={`${base}/termos`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-white/5">
              <FileText className="h-4 w-4 text-slate-500 dark:text-slate-400" />
              Termos de uso
            </Link>
            <Link href={`${base}/guias`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-white/5">
              <BookOpen className="h-4 w-4 text-slate-500 dark:text-slate-400" />
              Guias de uso
            </Link>
            <Link href={`/loja/${slug}/trocar-senha`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-white/5">
              <KeyRound className="h-4 w-4 text-slate-500 dark:text-slate-400" />
              Alterar senha
            </Link>
            <Link href={`/loja/${slug}/suporte`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-white/5">
              <CircleHelp className="h-4 w-4 text-slate-500 dark:text-slate-400" />
              Ajuda
            </Link>
          </div>
          <button
            type="button"
            onClick={onLogout}
            className="flex w-full items-center gap-2 border-t border-slate-100 px-4 py-2.5 text-left text-sm font-medium text-red-600 hover:bg-red-50 dark:border-white/10 dark:text-red-400 dark:hover:bg-red-950/40"
          >
            <LogOut className="h-4 w-4" />
            Sair
          </button>
        </div>
      )}
    </div>
  );
}
