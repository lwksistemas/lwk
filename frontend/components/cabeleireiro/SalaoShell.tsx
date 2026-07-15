'use client';

import { useState, type ReactNode } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LogOut, Menu, X } from 'lucide-react';
import type { LojaInfo } from '@/types/dashboard';
import {
  getSalaoNavHref,
  isSalaoNavActive,
  SALAO_NAV_ITEMS,
  SALAO_PRIMARY,
} from './salao-nav';

type Props = {
  loja: LojaInfo;
  onLogout?: () => void;
  children: ReactNode;
};

export function SalaoShell({ loja, onLogout, children }: Props) {
  const slug = loja.slug;
  const pathname = usePathname() || '';
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const primary = loja.cor_primaria || SALAO_PRIMARY;

  const Nav = ({ onNavigate }: { onNavigate?: () => void }) => (
    <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
      {SALAO_NAV_ITEMS.map((item) => {
        const active = isSalaoNavActive(pathname, slug, item.path);
        const Icon = item.icon;
        return (
          <Link
            key={item.path}
            href={getSalaoNavHref(slug, item.path)}
            onClick={() => onNavigate?.()}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              active ? 'bg-white/15 text-white font-medium' : 'text-white/80 hover:bg-white/10 hover:text-white'
            }`}
          >
            <Icon size={18} className="shrink-0 opacity-90" />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div
      className="flex min-h-screen"
      style={
        {
          '--salao-primary': primary,
          '--salao-accent': '#C4A4B0',
          '--salao-page-bg': '#F7F0F3',
        } as React.CSSProperties
      }
    >
      <aside
        className="hidden lg:flex w-60 flex-col text-white shrink-0"
        style={{ backgroundColor: primary }}
      >
        <div className="px-5 py-6 border-b border-white/10">
          <p
            className="text-3xl leading-none text-white"
            style={{ fontFamily: 'var(--font-salao-script, Georgia, serif)' }}
          >
            {loja.nome?.split(' ')[0] || 'Lumina'}
          </p>
          <p className="text-[10px] uppercase tracking-widest text-white/60 mt-2">Salão</p>
        </div>
        <Nav />
        <div className="p-4 border-t border-white/10">
          <p className="text-xs text-white/70 truncate">{loja.nome}</p>
          {onLogout && (
            <button
              type="button"
              onClick={onLogout}
              className="mt-3 flex items-center gap-2 text-sm text-white/80 hover:text-white"
            >
              <LogOut size={16} /> Sair
            </button>
          )}
        </div>
      </aside>

      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-[100] flex">
          <aside className="w-72 max-w-[85vw] flex flex-col text-white" style={{ backgroundColor: primary }}>
            <div className="flex items-center justify-between px-4 py-4 border-b border-white/10">
              <p className="text-2xl" style={{ fontFamily: 'var(--font-salao-script, Georgia, serif)' }}>
                {loja.nome?.split(' ')[0] || 'Lumina'}
              </p>
              <button type="button" onClick={() => setMobileOpen(false)} className="p-2">
                <X size={20} />
              </button>
            </div>
            <Nav onNavigate={() => setMobileOpen(false)} />
          </aside>
          <button type="button" className="flex-1 bg-black/40" aria-label="Fechar" onClick={() => setMobileOpen(false)} />
        </div>
      )}

      <div className="flex-1 min-w-0 flex flex-col bg-[var(--salao-page-bg)]">
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-200">
          <button type="button" onClick={() => setMobileOpen(true)} className="p-2 rounded-lg" style={{ color: primary }}>
            <Menu size={22} />
          </button>
          <button type="button" onClick={() => router.push(`/loja/${slug}/dashboard`)} className="font-semibold text-gray-900">
            {loja.nome}
          </button>
        </header>
        <main className="flex-1 min-h-0 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
