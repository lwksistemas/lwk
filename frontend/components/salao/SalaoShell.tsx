"use client";

import Link from "next/link";
import { useParams, usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Calendar, ChevronLeft, ChevronRight, LayoutDashboard, LogOut, Package, Receipt, Scissors, Settings, Users, UserRound, Wallet } from "lucide-react";
import { useLojaAuth } from "@/hooks/useLojaAuth";
import { SalaoAPI, type LocalRecebimentoSalao, type PainelSalao, type PapelSalao } from "@/lib/salao-api";

const ITENS = [
  { caminho: "", nome: "Visão geral", icone: LayoutDashboard },
  { caminho: "/agenda", nome: "Agenda", icone: Calendar },
  { caminho: "/clientes", nome: "Clientes", icone: Users },
  { caminho: "/servicos", nome: "Serviços", icone: Scissors },
  { caminho: "/profissionais", nome: "Profissionais", icone: UserRound },
  { caminho: "/estoque", nome: "Estoque", icone: Package },
  { caminho: "/caixa", nome: "Caixa/PDV", icone: Wallet },
  { caminho: "/financeiro", nome: "Financeiro", icone: Receipt },
  { caminho: "/configuracoes", nome: "Configurações", icone: Settings },
] as const;

const TEMAS: Record<PainelSalao, { barra: string; fundo: string; tinta: string }> = {
  operacao: { barra: "#7A3044", fundo: "#fbf6f4", tinta: "#3a2428" },
  semana: { barra: "#4c1d78", fundo: "#f6f4fb", tinta: "#2b2140" },
  gestao: { barra: "#3d5244", fundo: "#f7f4ee", tinta: "#243028" },
};

export function SalaoShell({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const pathname = usePathname();
  const router = useRouter();
  const slug = params.slug as string;
  const { handleLogout } = useLojaAuth(slug);
  const base = `/loja/${slug}/salao-cabeleireiro`;
  const [oculto, setOculto] = useState(false);
  const [painel, setPainel] = useState<PainelSalao>("operacao");
  const [cores, setCores] = useState({ menu: "", fundo: "" });
  const [papel, setPapel] = useState<PapelSalao | "">("");
  const [localRecebimento, setLocalRecebimento] = useState<LocalRecebimentoSalao>("caixa");
  const tema = TEMAS[painel];
  const barra = cores.menu || tema.barra;
  const fundo = cores.fundo || tema.fundo;

  useEffect(() => {
    setOculto(window.localStorage.getItem("salao-menu") === "oculto");
    document.cookie = "loja_usa_salao=1; path=/; max-age=86400; SameSite=Lax";
    document.cookie = "loja_usa_crm=; path=/; max-age=0";
    SalaoAPI.config().then((dados) => {
      setPainel(dados.painel);
      setCores({ menu: dados.cor_primaria || "", fundo: dados.cor_fundo_pagina || "" });
      if (dados.papel) setPapel(dados.papel);
      if (dados.local_recebimento) setLocalRecebimento(dados.local_recebimento);
    }).catch(() => undefined);
    function aoTrocar(evento: Event) {
      const proximo = (evento as CustomEvent<PainelSalao>).detail;
      if (proximo === "operacao" || proximo === "gestao" || proximo === "semana") setPainel(proximo);
    }
    window.addEventListener("salao-painel", aoTrocar);
    return () => window.removeEventListener("salao-painel", aoTrocar);
  }, [pathname]);

  useEffect(() => {
    if (papel !== "recepcionista") return;
    if (pathname.startsWith(`${base}/caixa`)) return;
    router.replace(`${base}/caixa`);
  }, [papel, pathname, base, router]);

  function itemVisivel(caminho: string) {
    if (!papel || papel === "administrador" || papel === "autonomo") return true;
    if (papel === "recepcionista") return caminho === "/caixa";
    if (caminho === "" || caminho === "/agenda") return true;
    if (caminho === "/caixa") return localRecebimento !== "agenda";
    return false;
  }

  function alternarMenu() {
    const proximo = !oculto;
    setOculto(proximo);
    window.localStorage.setItem("salao-menu", proximo ? "oculto" : "visivel");
  }

  return (
    <div className={`min-h-screen ${oculto ? "grid grid-cols-[4.25rem_minmax(0,1fr)]" : "grid grid-cols-1 md:grid-cols-[240px_minmax(0,1fr)]"}`} style={{ background: fundo, color: tema.tinta }}>
      <aside className={`sticky top-0 flex h-screen flex-col overflow-y-auto text-white ${oculto ? "items-center px-2 py-3" : "p-4"}`} style={{ background: barra }}>
        <div className={`mb-3 flex items-center gap-2 ${oculto ? "justify-center" : "justify-between"}`}>
          {oculto ? null : <p className="px-2 text-2xl font-semibold">Salão</p>}
          <button type="button" onClick={alternarMenu} className="grid h-8 w-8 place-items-center rounded-lg bg-white/15" title={oculto ? "Mostrar menu" : "Ocultar menu"} aria-label={oculto ? "Mostrar menu" : "Ocultar menu"}>
            {oculto ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>
        <nav className="flex flex-1 flex-col gap-1">
          {ITENS.filter(({ caminho }) => itemVisivel(caminho)).map(({ caminho, nome, icone: Icone }) => {
            const href = `${base}${caminho}`;
            const ativo = caminho === "" ? pathname === base : pathname.startsWith(href);
            return (
              <Link key={nome} href={href} title={nome} aria-label={nome} className={`flex items-center gap-2 rounded-lg text-sm ${oculto ? "justify-center px-2 py-2" : "px-3 py-2"} ${ativo ? "bg-white/20" : "hover:bg-white/10"}`}>
                <Icone size={18} className="shrink-0" />
                {oculto ? null : nome}
              </Link>
            );
          })}
        </nav>
        <button type="button" onClick={handleLogout} title="Sair" aria-label="Sair" className={`mt-4 flex items-center gap-2 rounded-lg text-sm text-white/80 hover:bg-white/10 ${oculto ? "justify-center px-2 py-2" : "px-3 py-2"}`}>
          <LogOut size={18} className="shrink-0" />
          {oculto ? null : "Sair"}
        </button>
      </aside>
      <div className="min-w-0 p-4 sm:p-5">
        {children}
      </div>
    </div>
  );
}
