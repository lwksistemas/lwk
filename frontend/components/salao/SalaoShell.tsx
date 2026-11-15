"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { SalaoAPI, type PainelSalao } from "@/lib/salao-api";

const ITENS = [
  ["", "Visão geral"],
  ["/agenda", "Agenda"],
  ["/clientes", "Clientes"],
  ["/servicos", "Serviços"],
  ["/profissionais", "Profissionais"],
  ["/financeiro", "Financeiro"],
  ["/configuracoes", "Configurações"],
] as const;

const TEMAS: Record<PainelSalao, { barra: string; fundo: string; tinta: string }> = {
  operacao: { barra: "#7A3044", fundo: "#fbf6f4", tinta: "#3a2428" },
  semana: { barra: "#4c1d78", fundo: "#f6f4fb", tinta: "#2b2140" },
  gestao: { barra: "#3d5244", fundo: "#f7f4ee", tinta: "#243028" },
};

export function SalaoShell({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const pathname = usePathname();
  const slug = params.slug as string;
  const base = `/loja/${slug}/salao-cabeleireiro`;
  const [oculto, setOculto] = useState(false);
  const [painel, setPainel] = useState<PainelSalao>("operacao");
  const tema = TEMAS[painel];

  useEffect(() => {
    setOculto(window.localStorage.getItem("salao-menu") === "oculto");
    document.cookie = "loja_usa_salao=1; path=/; max-age=86400; SameSite=Lax";
    document.cookie = "loja_usa_crm=; path=/; max-age=0";
    SalaoAPI.config().then((dados) => setPainel(dados.painel)).catch(() => undefined);
    function aoTrocar(evento: Event) {
      const proximo = (evento as CustomEvent<PainelSalao>).detail;
      if (proximo === "operacao" || proximo === "gestao" || proximo === "semana") setPainel(proximo);
    }
    window.addEventListener("salao-painel", aoTrocar);
    return () => window.removeEventListener("salao-painel", aoTrocar);
  }, []);

  function alternarMenu() {
    const proximo = !oculto;
    setOculto(proximo);
    window.localStorage.setItem("salao-menu", proximo ? "oculto" : "visivel");
  }

  return (
    <div className="min-h-screen" style={{ display: "grid", gridTemplateColumns: oculto ? "1fr" : "240px 1fr", background: tema.fundo, color: tema.tinta }}>
      {oculto ? (
        <button type="button" onClick={alternarMenu} className="fixed left-3 top-3 z-20 rounded-full bg-white px-3 py-1.5 text-sm shadow">
          Mostrar menu
        </button>
      ) : (
        <aside className="flex min-h-screen flex-col p-4 text-white" style={{ background: tema.barra }}>
          <p className="px-2 pb-4 text-2xl font-semibold">Salão</p>
          <nav className="flex flex-1 flex-col gap-1">
            {ITENS.map(([caminho, nome]) => {
              const href = `${base}${caminho}`;
              const ativo = caminho === "" ? pathname === base : pathname.startsWith(href);
              return (
                <Link key={nome} href={href} className={`rounded-lg px-3 py-2 text-sm ${ativo ? "bg-white/20" : "hover:bg-white/10"}`}>
                  {nome}
                </Link>
              );
            })}
          </nav>
          <button type="button" onClick={alternarMenu} className="mt-4 rounded-lg px-3 py-2 text-left text-sm text-white/80 hover:bg-white/10">
            Ocultar menu
          </button>
        </aside>
      )}
      <div className="min-w-0 p-5">{children}</div>
    </div>
  );
}
