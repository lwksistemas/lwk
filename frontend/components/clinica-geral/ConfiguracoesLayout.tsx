'use client';

import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';
import { useState, type ReactNode } from 'react';
import { TEAL } from '@/lib/clinica-geral-theme';
import {
  AJUSTES_MENU,
  CONSULTORIO_MENU,
  PERFIL_SUBMENU,
  abaConfigAtiva,
  clinicaBase,
  perfilSubmenuAtivo,
  type AbaConfig,
} from '@/lib/clinica-config-nav';

type ConfiguracoesLayoutProps = {
  children: ReactNode;
};

const ABAS: { id: AbaConfig; label: string; href?: string }[] = [
  { id: 'perfil', label: 'Perfil' },
  { id: 'consultorio', label: 'Meu consultório' },
  { id: 'ajustes', label: 'Ajustes' },
  { id: 'integracoes', label: 'Integrações' },
  { id: 'extras', label: 'Extras' },
];

export function ConfiguracoesLayout({ children }: ConfiguracoesLayoutProps) {
  const params = useParams();
  const pathname = usePathname();
  const slug = (params?.slug as string) ?? '';
  const base = clinicaBase(slug);
  const aba = abaConfigAtiva(pathname);
  const sub = perfilSubmenuAtivo(pathname);
  const [aberto, setAberto] = useState<AbaConfig | null>(null);

  const hrefAba = (id: AbaConfig) => {
    if (id === 'perfil') return `${base}/perfil`;
    if (id === 'integracoes') return `/loja/${slug}/configuracoes/whatsapp`;
    if (id === 'extras') return `${base}/configuracoes`;
    return null;
  };

  return (
    <div className="min-h-full bg-white dark:bg-[#16152B]">
      <div className="px-6 pt-6 sm:px-10">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Configurações</h1>
        <nav className="mt-4 flex flex-wrap gap-x-6 gap-y-1 border-b border-slate-200 dark:border-white/10">
          {ABAS.map((item) => {
            const ativo = aba === item.id;
            const temMenu = item.id === 'consultorio' || item.id === 'ajustes';
            const destino = hrefAba(item.id);
            return (
              <div
                key={item.id}
                className="relative"
                onMouseEnter={() => temMenu && setAberto(item.id)}
                onMouseLeave={() => setAberto((atual) => (atual === item.id ? null : atual))}
              >
                {destino ? (
                  <Link
                    href={destino}
                    className={`inline-block px-1 pb-2 text-sm ${
                      ativo ? 'font-semibold text-slate-800 dark:text-white' : 'text-slate-600 hover:text-slate-800 dark:text-slate-300'
                    }`}
                    style={ativo ? { boxShadow: `inset 0 -2px 0 ${TEAL}` } : undefined}
                  >
                    {item.label}
                  </Link>
                ) : (
                  <button
                    type="button"
                    className={`inline-block px-1 pb-2 text-sm ${
                      ativo ? 'font-semibold text-slate-800 dark:text-white' : 'text-slate-600 hover:text-slate-800 dark:text-slate-300'
                    }`}
                    style={ativo ? { boxShadow: `inset 0 -2px 0 ${TEAL}` } : undefined}
                    onClick={() => setAberto((atual) => (atual === item.id ? null : item.id))}
                  >
                    {item.label}
                  </button>
                )}
                {temMenu && aberto === item.id ? (
                  <div className="absolute left-0 top-full z-30 min-w-[280px] rounded-md border border-slate-200 bg-white py-1 shadow-lg dark:border-white/10 dark:bg-[#1E1D3A]">
                    {(item.id === 'consultorio' ? CONSULTORIO_MENU : AJUSTES_MENU).map((opt) => (
                      <Link
                        key={opt.suffix}
                        href={`${base}/${opt.suffix}`}
                        className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-white/5"
                        onClick={() => setAberto(null)}
                      >
                        {opt.label}
                      </Link>
                    ))}
                  </div>
                ) : null}
              </div>
            );
          })}
        </nav>
      </div>

      <div className={`px-6 py-6 sm:px-10 ${aba === 'perfil' ? 'flex gap-8' : ''}`}>
        {aba === 'perfil' ? (
          <aside className="w-44 shrink-0">
            <nav className="space-y-0.5">
              {PERFIL_SUBMENU.map((item) => {
                const ativo = sub === item.id;
                return (
                  <Link
                    key={item.id}
                    href={`${base}/${item.suffix}`}
                    className={`block rounded-sm px-3 py-2 text-sm ${
                      ativo
                        ? 'bg-slate-100 font-medium text-slate-800 dark:bg-white/10 dark:text-white'
                        : 'text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-white/5'
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </aside>
        ) : null}
        <div className="min-w-0 flex-1">{children}</div>
      </div>
    </div>
  );
}
