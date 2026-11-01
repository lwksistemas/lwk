'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ChevronDown, Menu, X } from "lucide-react";
import AcessoRapidoModal from "./AcessoRapidoModal";

export interface HeaderLink {
  label: string;
  href: string;
}

interface HeaderProps {
  solucoes?: HeaderLink[];
  whatsappUrl?: string | null;
}

const SOLUCOES_PADRAO: HeaderLink[] = [
  { label: "CRM Vendas", href: "/solucoes/crm-vendas" },
  { label: "Gestão para Clínicas de Estética", href: "/solucoes/clinicas-estetica" },
  { label: "Sistemas Personalizados", href: "/solucoes/personalizados" },
];

function rotuloPublico(label: string) {
  if (
    label === "CRM de Vendas" ||
    label === "CRM de Vendas — LWK Sales Cloud" ||
    label === "LWK Sales Cloud — CRM de Vendas" ||
    label === "LWK Sales Cloud"
  ) {
    return "CRM Vendas";
  }
  return label;
}

function classeAtual(ativo: boolean) {
  return ativo
    ? "text-[1.05rem] font-semibold text-white underline decoration-[3px] underline-offset-8"
    : "text-[1.05rem] font-medium text-white/95 hover:text-white";
}

function MenuSuspenso({
  label,
  itens,
  ativo,
}: {
  label: string;
  itens: HeaderLink[];
  ativo: boolean;
}) {
  const [aberto, setAberto] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!aberto) return;
    function fechar(evento: PointerEvent) {
      if (!ref.current?.contains(evento.target as Node)) setAberto(false);
    }
    function tecla(evento: KeyboardEvent) {
      if (evento.key === "Escape") setAberto(false);
    }
    document.addEventListener("pointerdown", fechar);
    document.addEventListener("keydown", tecla);
    return () => {
      document.removeEventListener("pointerdown", fechar);
      document.removeEventListener("keydown", tecla);
    };
  }, [aberto]);

  return (
    <div
      ref={ref}
      className="relative"
      onMouseEnter={() => setAberto(true)}
      onMouseLeave={() => setAberto(false)}
    >
      <button
        type="button"
        className={`inline-flex items-center gap-1 ${classeAtual(ativo)}`}
        aria-expanded={aberto}
        aria-haspopup="true"
        aria-current={ativo ? "page" : undefined}
        onClick={() => {
          const comMouse = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
          if (comMouse) {
            setAberto(true);
            return;
          }
          setAberto((valor) => !valor);
        }}
      >
        {label}
        <ChevronDown className="h-4 w-4 opacity-80" aria-hidden />
      </button>
      {itens.length > 0 && (
        <div className={`${aberto ? "visible opacity-100" : "invisible opacity-0"} absolute left-0 top-full z-20 min-w-72 pt-2 transition`}>
          <div className="rounded-xl border border-white/10 bg-[#0c2348] p-2 shadow-xl">
            {itens.map((item) => (
              <Link
                key={item.href + item.label}
                href={item.href}
                className="block rounded-lg px-3 py-2 text-sm text-slate-100 hover:bg-white/10"
                onClick={() => setAberto(false)}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Header({ solucoes = [], whatsappUrl }: HeaderProps) {
  const pathname = usePathname();
  const [aberto, setAberto] = useState(false);
  const [acessoAberto, setAcessoAberto] = useState(false);
  const contato = whatsappUrl || "/contato";
  const itensSolucoes = (solucoes.length > 0 ? solucoes : SOLUCOES_PADRAO).map((item) => ({
    ...item,
    label: rotuloPublico(item.label),
  }));
  const naHome = pathname === "/";
  const emSolucoes = pathname.startsWith("/solucoes");
  const emSegmentos = pathname.startsWith("/segmentos");
  const emPlanos = pathname.startsWith("/planos");
  const emContato = pathname.startsWith("/contato");

  useEffect(() => {
    setAberto(false);
  }, [pathname]);

  return (
    <header className="sticky top-0 z-50 w-full bg-[#04183f]">
      <div className="flex w-full items-center gap-4 px-4 py-2 sm:px-6 lg:px-8">
        <Link href="/" className="flex shrink-0 items-center gap-2" aria-label="LWK Sistemas — página inicial">
          <img src="/homepage/logo-mark.png" alt="" className="h-[4.35rem] w-auto" />
          <span className="leading-none">
            <span
              className="block text-[2.55rem] font-black tracking-[-0.04em]"
              style={{
                backgroundImage: "linear-gradient(180deg, #e9fcff 0%, #3ec4ff 46%, #1476e2 100%)",
                WebkitBackgroundClip: "text",
                backgroundClip: "text",
                color: "transparent",
              }}
            >
              LWK
            </span>
            <span className="-mt-1 block text-center text-[0.78rem] font-semibold tracking-[0.2em] text-[#d7e7f8]">
              SISTEMAS
            </span>
          </span>
        </Link>

        <nav className="hidden min-w-0 flex-1 items-center justify-center gap-x-8 md:flex lg:gap-x-11" aria-label="Principal">
          <Link href="/#inicio" className={classeAtual(naHome)} aria-current={naHome ? "page" : undefined}>
            Início
          </Link>
          <MenuSuspenso label="Soluções" itens={itensSolucoes} ativo={emSolucoes} />
          <Link href="/segmentos" className={classeAtual(emSegmentos)} aria-current={emSegmentos ? "page" : undefined}>
            Segmentos
          </Link>
          <Link href="/planos" className={classeAtual(emPlanos)} aria-current={emPlanos ? "page" : undefined}>
            Planos
          </Link>
          <Link href="/contato" className={classeAtual(emContato)} aria-current={emContato ? "page" : undefined}>
            Contato
          </Link>
          <button
            type="button"
            onClick={() => setAcessoAberto(true)}
            className="shrink-0 rounded-full border border-white/50 px-4 py-1.5 text-[1.02rem] font-semibold text-white hover:bg-white/10"
          >
            Acessar sistemas
          </button>
        </nav>
        <a
          href={contato}
          target={whatsappUrl ? "_blank" : undefined}
          rel={whatsappUrl ? "noopener noreferrer" : undefined}
          className="hidden shrink-0 items-center gap-2 rounded-full bg-[#25D366] px-4 py-2 text-[1.02rem] font-semibold text-white shadow-md hover:bg-[#1ebe5a] md:inline-flex"
        >
            <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current" aria-hidden>
              <path d="M12.04 2C6.58 2 2.15 6.4 2.15 11.83c0 1.74.46 3.44 1.34 4.94L2 22l5.39-1.4a10.1 10.1 0 0 0 4.65 1.14h.01c5.46 0 9.89-4.4 9.89-9.83C21.94 6.4 17.5 2 12.04 2Zm5.76 13.95c-.24.68-1.4 1.3-1.94 1.38-.5.07-1.12.1-1.81-.11-.42-.13-.95-.3-1.64-.59-2.88-1.24-4.76-4.14-4.9-4.33-.14-.19-1.15-1.53-1.15-2.92 0-1.39.73-2.07.99-2.35.26-.28.57-.35.76-.35.19 0 .38 0 .55.01.18.01.41-.07.64.49.24.58.81 2 .88 2.15.07.14.12.32.02.51-.09.19-.14.31-.28.48-.14.16-.29.37-.42.49-.14.14-.28.29-.12.56.16.28.71 1.17 1.52 1.9 1.05.94 1.93 1.23 2.2 1.37.28.14.44.12.6-.07.16-.19.68-.79.86-1.06.18-.28.36-.23.6-.14.24.09 1.54.73 1.8.86.26.14.44.2.5.31.07.12.07.67-.17 1.35Z" />
            </svg>
            Fale Conosco
          </a>

        <button
          type="button"
          className="rounded-lg p-2 text-white md:hidden"
          aria-label={aberto ? "Fechar menu" : "Abrir menu"}
          aria-expanded={aberto}
          onClick={() => setAberto((v) => !v)}
        >
          {aberto ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {aberto && (
        <nav className="border-t border-white/10 px-4 py-3 md:hidden" aria-label="Menu móvel">
          <Link href="/#inicio" className="block py-2 text-white">Início</Link>
          <p className="py-2 text-slate-200">Soluções</p>
          {itensSolucoes.map((item) => (
            <Link key={item.href + item.label} href={item.href} className="block py-1 pl-3 text-sm text-slate-300">
              {item.label}
            </Link>
          ))}
          <Link href="/segmentos" className="block py-2 text-slate-200">Segmentos</Link>
          <Link href="/planos" className="block py-2 text-slate-200">Planos</Link>
          <Link href="/contato" className="block py-2 text-slate-200">Contato</Link>
          <button
            type="button"
            onClick={() => {
              setAberto(false);
              setAcessoAberto(true);
            }}
            className="mt-2 inline-flex rounded-full border border-white/50 px-4 py-2 text-sm font-semibold text-white"
          >
            Acessar sistemas
          </button>
          <a
            href={contato}
            target={whatsappUrl ? "_blank" : undefined}
            rel={whatsappUrl ? "noopener noreferrer" : undefined}
            className="mt-2 inline-flex items-center gap-2 rounded-full bg-[#25D366] px-4 py-2 text-sm font-semibold text-white"
          >
            Fale Conosco
          </a>
        </nav>
      )}
      <AcessoRapidoModal isOpen={acessoAberto} onClose={() => setAcessoAberto(false)} />
    </header>
  );
}
