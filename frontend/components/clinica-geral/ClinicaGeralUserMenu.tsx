'use client';

import Link from 'next/link';
import { BookOpen, ChevronDown, CircleHelp, FileText, KeyRound, LogOut, Settings, UserRound } from 'lucide-react';

type ClinicaGeralUserMenuProps = {
  base: string;
  slug: string;
  lojaNome: string;
  usuario: { nome: string; email: string };
  aberto: boolean;
  onToggle: () => void;
  onClose: () => void;
  onLogout: () => void;
};

export function ClinicaGeralUserMenu({
  base,
  slug,
  lojaNome,
  usuario,
  aberto,
  onToggle,
  onClose,
  onLogout,
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
        <div className="absolute right-0 mt-1 w-72 overflow-hidden rounded-md border border-slate-200 bg-white text-slate-800 shadow-lg">
          <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-sm font-medium text-slate-600">
              {(usuario.nome || lojaNome).slice(0, 1).toUpperCase()}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{usuario.nome || lojaNome}</p>
              {usuario.email ? <p className="truncate text-xs text-slate-500">{usuario.email}</p> : null}
            </div>
          </div>
          <div className="py-1">
            <Link href={`${base}/perfil`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
              <UserRound className="h-4 w-4 text-slate-500" />
              Meu perfil
            </Link>
            <Link href={`${base}/configuracoes`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
              <Settings className="h-4 w-4 text-slate-500" />
              Configurações
            </Link>
            <Link href={`${base}/termos`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
              <FileText className="h-4 w-4 text-slate-500" />
              Termos de uso
            </Link>
            <Link href={`${base}/guias`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
              <BookOpen className="h-4 w-4 text-slate-500" />
              Guias de uso
            </Link>
            <Link href={`/loja/${slug}/trocar-senha`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
              <KeyRound className="h-4 w-4 text-slate-500" />
              Alterar senha
            </Link>
            <Link href={`/loja/${slug}/suporte`} onClick={onClose} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
              <CircleHelp className="h-4 w-4 text-slate-500" />
              Ajuda
            </Link>
          </div>
          <button
            type="button"
            onClick={onLogout}
            className="flex w-full items-center gap-2 border-t border-slate-100 px-4 py-2.5 text-left text-sm font-medium text-red-600 hover:bg-red-50"
          >
            <LogOut className="h-4 w-4" />
            Sair
          </button>
        </div>
      )}
    </div>
  );
}
