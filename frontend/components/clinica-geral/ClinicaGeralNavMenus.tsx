'use client';

import Link from 'next/link';
import { useState, type ReactNode } from 'react';
import { TEAL } from '@/lib/clinica-geral-theme';
import { RECURSOS_MENU, RELATORIOS_MENU } from '@/lib/clinica-geral-types';

type MenuAberto = 'relatorios' | 'recursos' | null;

type ClinicaGeralNavMenusProps = {
  slug: string;
  base: string;
  active: string;
};

export function ClinicaGeralNavMenus({ slug, base, active }: ClinicaGeralNavMenusProps) {
  const [aberto, setAberto] = useState<MenuAberto>(null);

  return (
    <>
      <NavDropdown
        label="relatórios"
        active={active === 'relatorios'}
        open={aberto === 'relatorios'}
        align="left"
        onOpen={() => setAberto('relatorios')}
        onClose={() => setAberto((atual) => (atual === 'relatorios' ? null : atual))}
      >
        {RELATORIOS_MENU.map((opt) => (
          <Link
            key={opt.tipo}
            href={`${base}/relatorios/${opt.tipo}`}
            onClick={() => setAberto(null)}
            className="block px-4 py-2 text-sm lowercase hover:bg-slate-50"
          >
            {opt.label}
          </Link>
        ))}
      </NavDropdown>
      <NavDropdown
        label="recursos"
        active={active === 'recursos'}
        open={aberto === 'recursos'}
        align="right"
        onOpen={() => setAberto('recursos')}
        onClose={() => setAberto((atual) => (atual === 'recursos' ? null : atual))}
      >
        {RECURSOS_MENU.map((opt) => (
          <Link
            key={opt.label}
            href={opt.path(slug)}
            onClick={() => setAberto(null)}
            className="block px-4 py-2 text-sm lowercase hover:bg-slate-50"
          >
            {opt.label}
          </Link>
        ))}
      </NavDropdown>
    </>
  );
}

function NavDropdown({
  label,
  active,
  open,
  align,
  onOpen,
  onClose,
  children,
}: {
  label: string;
  active: boolean;
  open: boolean;
  align: 'left' | 'right';
  onOpen: () => void;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <div className="relative" onMouseEnter={onOpen} onMouseLeave={onClose}>
      <button
        type="button"
        onClick={() => (open ? onClose() : onOpen())}
        className={`px-2 py-3 lowercase ${active ? 'font-medium' : 'text-white/80 hover:text-white'}`}
        style={active ? { boxShadow: `inset 0 -3px 0 ${TEAL}` } : undefined}
        aria-expanded={open}
        aria-haspopup="menu"
      >
        {label}
      </button>
      {open ? (
        <div
          role="menu"
          className={`absolute top-full z-50 min-w-[220px] rounded-md bg-white py-1 text-slate-700 shadow-lg ${
            align === 'right' ? 'right-0' : 'left-0'
          }`}
        >
          {children}
        </div>
      ) : null}
    </div>
  );
}
