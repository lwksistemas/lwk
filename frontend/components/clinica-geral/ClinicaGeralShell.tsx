'use client';

import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from 'react';
import {
  Bell,
  BookOpen,
  ChevronDown,
  CircleHelp,
  FileText,
  KeyRound,
  LayoutGrid,
  LogOut,
  Search,
  Settings,
  UserRound,
} from 'lucide-react';
import type { LojaInfo } from '@/types/dashboard';
import { MiniCalendario } from '@/components/clinica-geral/MiniCalendario';
import { TarefasDoDia } from '@/components/clinica-geral/TarefasDoDia';
import { getUsuarioConsultorio } from '@/lib/clinica-geral-api';
import { RELATORIOS_MENU, RECURSOS_MENU } from '@/lib/clinica-geral-types';
import { readSidebarHidden, toISODate, writeSidebarHidden } from '@/lib/clinica-geral-utils';

const NAVY = '#2F2E5B';
const TEAL = '#0D9B9B';

const NAV = [
  { id: 'agenda', label: 'agenda', suffix: 'agenda' },
  { id: 'pacientes', label: 'pacientes', suffix: 'pacientes' },
  { id: 'relatorios', label: 'relatórios', suffix: 'relatorios' },
  { id: 'recursos', label: 'recursos', suffix: 'recursos' },
] as const;

type ClinicaGeralShellProps = {
  loja: LojaInfo;
  slug: string;
  onLogout: () => void;
  children: ReactNode;
};

export function ClinicaGeralShell({ loja, slug, onLogout, children }: ClinicaGeralShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const search = useSearchParams();
  const base = `/loja/${slug}/clinica-geral`;
  const agendaData = search.get('data') || toISODate(new Date());
  const [sidebarHidden, setSidebarHidden] = useState(false);
  const [busca, setBusca] = useState('');
  const [menuUser, setMenuUser] = useState(false);
  const [menuRelatorios, setMenuRelatorios] = useState(false);
  const [menuRecursos, setMenuRecursos] = useState(false);
  const [usuario, setUsuario] = useState({ nome: loja.nome, email: '' });

  useEffect(() => {
    setSidebarHidden(readSidebarHidden());
  }, []);

  useEffect(() => {
    void getUsuarioConsultorio()
      .then((u) => setUsuario({ nome: u.nome || loja.nome, email: u.email }))
      .catch(() => setUsuario({ nome: loja.nome, email: '' }));
  }, [loja.nome]);

  const toggleSidebar = () => {
    setSidebarHidden((prev) => {
      const next = !prev;
      writeSidebarHidden(next);
      return next;
    });
  };

  const active = useMemo(() => {
    if (pathname.includes('/pacientes')) return 'pacientes';
    if (pathname.includes('/relatorios')) return 'relatorios';
    if (
      pathname.includes('/recursos') ||
      pathname.includes('/configuracoes') ||
      pathname.includes('/tiss') ||
      pathname.includes('/faturamento')
    ) {
      return 'recursos';
    }
    return 'agenda';
  }, [pathname]);

  const onSearch = (e: FormEvent) => {
    e.preventDefault();
    const q = busca.trim();
    router.push(q ? `${base}/pacientes?q=${encodeURIComponent(q)}` : `${base}/pacientes`);
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#F7F8FB] text-slate-800">
      <header className="sticky top-0 z-40 text-white" style={{ backgroundColor: NAVY }}>
        <div className="flex h-14 items-center gap-3 px-3 sm:px-4">
          <button
            type="button"
            onClick={toggleSidebar}
            className="shrink-0 rounded p-1.5 text-white/90 hover:bg-white/10"
            title={sidebarHidden ? 'Mostrar menu esquerdo' : 'Ocultar menu esquerdo'}
            aria-label={sidebarHidden ? 'Mostrar menu esquerdo' : 'Ocultar menu esquerdo'}
            aria-pressed={!sidebarHidden}
          >
            <LayoutGrid className="h-5 w-5" />
          </button>

          <Link href={`${base}/agenda`} className="hidden shrink-0 items-center gap-2 sm:flex">
            <span
              className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold"
              style={{ backgroundColor: TEAL }}
            >
              CG
            </span>
            <span className="max-w-[160px] truncate text-sm font-medium lowercase tracking-wide">
              {loja.nome}
            </span>
          </Link>

          <form onSubmit={onSearch} className="mx-auto hidden min-w-0 max-w-md flex-1 md:block">
            <label className="flex items-center gap-2 rounded-md bg-white/10 px-3 py-1.5">
              <Search className="h-4 w-4 text-white/70" />
              <input
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="buscar pacientes"
                className="w-full bg-transparent text-sm text-white placeholder:text-white/55 outline-none"
              />
            </label>
          </form>

          <nav className="ml-auto flex items-center gap-1 text-sm sm:gap-2">
            {NAV.map((item) => {
              const href = `${base}/${item.suffix}`;
              const isActive = active === item.id;
              if (item.id === 'relatorios' || item.id === 'recursos') {
                const aberto = item.id === 'relatorios' ? menuRelatorios : menuRecursos;
                const setAberto = item.id === 'relatorios' ? setMenuRelatorios : setMenuRecursos;
                return (
                  <div
                    key={item.id}
                    className="relative"
                    onMouseEnter={() => setAberto(true)}
                    onMouseLeave={() => setAberto(false)}
                  >
                    <button
                      type="button"
                      onClick={() => setAberto((v) => !v)}
                      className={`px-2 py-3 lowercase ${isActive ? 'font-medium' : 'text-white/80 hover:text-white'}`}
                      style={isActive ? { boxShadow: `inset 0 -3px 0 ${TEAL}` } : undefined}
                    >
                      {item.label}
                    </button>
                    {aberto && (
                      <div className="absolute right-0 top-full z-50 min-w-[220px] rounded-md bg-white py-1 text-slate-700 shadow-lg">
                        {item.id === 'relatorios'
                          ? RELATORIOS_MENU.map((opt) => (
                              <Link
                                key={opt.tipo}
                                href={`${base}/relatorios/${opt.tipo}`}
                                onClick={() => setAberto(false)}
                                className="block px-4 py-2 text-sm lowercase hover:bg-slate-50"
                              >
                                {opt.label}
                              </Link>
                            ))
                          : RECURSOS_MENU.map((opt) => (
                              <Link
                                key={opt.label}
                                href={opt.path(slug)}
                                onClick={() => setAberto(false)}
                                className="block px-4 py-2 text-sm lowercase hover:bg-slate-50"
                              >
                                {opt.label}
                              </Link>
                            ))}
                      </div>
                    )}
                  </div>
                );
              }
              return (
                <Link
                  key={item.id}
                  href={href}
                  className={`px-2 py-3 lowercase ${isActive ? 'font-medium' : 'text-white/80 hover:text-white'}`}
                  style={isActive ? { boxShadow: `inset 0 -3px 0 ${TEAL}` } : undefined}
                >
                  {item.label}
                </Link>
              );
            })}
            <button type="button" className="ml-1 rounded p-2 text-white/80 hover:bg-white/10" title="Notificações">
              <Bell className="h-4 w-4" />
            </button>
            <div className="relative">
              <button
                type="button"
                onClick={() => setMenuUser((v) => !v)}
                className="flex items-center gap-1 rounded p-1.5 hover:bg-white/10"
                aria-label="Menu do usuário"
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/20 text-xs">
                  {loja.nome.slice(0, 1).toUpperCase()}
                </span>
                <ChevronDown className="h-3.5 w-3.5" />
              </button>
              {menuUser && (
                <div className="absolute right-0 mt-1 w-72 overflow-hidden rounded-md border border-slate-200 bg-white text-slate-800 shadow-lg">
                  <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-sm font-medium text-slate-600">
                      {(usuario.nome || loja.nome).slice(0, 1).toUpperCase()}
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{usuario.nome || loja.nome}</p>
                      {usuario.email ? (
                        <p className="truncate text-xs text-slate-500">{usuario.email}</p>
                      ) : null}
                    </div>
                  </div>
                  <div className="py-1">
                    <Link href={`${base}/perfil`} onClick={() => setMenuUser(false)} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
                      <UserRound className="h-4 w-4 text-slate-500" />
                      Meu perfil
                    </Link>
                    <Link href={`${base}/configuracoes`} onClick={() => setMenuUser(false)} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
                      <Settings className="h-4 w-4 text-slate-500" />
                      Configurações
                    </Link>
                    <Link href={`${base}/termos`} onClick={() => setMenuUser(false)} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
                      <FileText className="h-4 w-4 text-slate-500" />
                      Termos de uso
                    </Link>
                    <Link href={`${base}/guias`} onClick={() => setMenuUser(false)} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
                      <BookOpen className="h-4 w-4 text-slate-500" />
                      Guias de uso
                    </Link>
                    <Link href={`/loja/${slug}/trocar-senha`} onClick={() => setMenuUser(false)} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
                      <KeyRound className="h-4 w-4 text-slate-500" />
                      Alterar senha
                    </Link>
                    <Link href={`/loja/${slug}/suporte`} onClick={() => setMenuUser(false)} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50">
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
          </nav>
        </div>
        <form onSubmit={onSearch} className="border-t border-white/10 px-3 py-2 md:hidden">
          <label className="flex items-center gap-2 rounded-md bg-white/10 px-3 py-1.5">
            <Search className="h-4 w-4 text-white/70" />
            <input
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="buscar pacientes"
              className="w-full bg-transparent text-sm text-white placeholder:text-white/55 outline-none"
            />
          </label>
        </form>
      </header>

      <div className="flex min-h-0 flex-1">
        {!sidebarHidden && (
          <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:flex lg:flex-col">
            <div className="p-4">
              {active === 'agenda' && (
                <button
                  type="button"
                  onClick={() => router.push(`${base}/agenda?data=${agendaData}&nova=1`)}
                  className="mb-4 w-full rounded-md py-2 text-sm font-medium text-white"
                  style={{ backgroundColor: TEAL }}
                >
                  nova consulta
                </button>
              )}
              <MiniCalendario
                selected={agendaData}
                onSelect={(iso) => router.push(`${base}/agenda?data=${iso}`)}
              />
            </div>
            <TarefasDoDia data={agendaData} />
          </aside>
        )}

        {sidebarHidden && (
          <div className="hidden w-8 shrink-0 flex-col items-center border-r border-slate-200 bg-slate-50 pt-3 lg:flex">
            <button
              type="button"
              onClick={toggleSidebar}
              className="rounded p-1 text-slate-500 hover:bg-slate-200"
              title="Mostrar menu esquerdo"
              aria-label="Mostrar menu esquerdo"
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
          </div>
        )}

        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
