"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const ITENS = [
  ["", "Visão geral"],
  ["/agenda", "Agenda"],
  ["/clientes", "Clientes"],
  ["/servicos", "Serviços"],
  ["/profissionais", "Profissionais"],
  ["/financeiro", "Financeiro"],
  ["/configuracoes", "Configurações"],
] as const;

export function SalaoShell({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const pathname = usePathname();
  const slug = params.slug as string;
  const base = `/loja/${slug}/salao-cabeleireiro`;
  const [oculto, setOculto] = useState(false);

  useEffect(() => {
    setOculto(window.localStorage.getItem("salao-menu") === "oculto");
    document.cookie = "loja_usa_salao=1; path=/; max-age=86400; SameSite=Lax";
    document.cookie = "loja_usa_crm=; path=/; max-age=0";
  }, []);

  function alternarMenu() {
    const proximo = !oculto;
    setOculto(proximo);
    window.localStorage.setItem("salao-menu", proximo ? "oculto" : "visivel");
  }

  return (
    <div className="min-h-screen bg-[#fbf7f5] text-[#3a2428]" style={{ display: "grid", gridTemplateColumns: oculto ? "1fr" : "232px 1fr" }}>
      {oculto ? null : (
        <aside className="min-h-screen bg-[#7a3044] text-white p-4">
          <p className="px-2 pb-4 text-2xl font-semibold">Salão</p>
          <nav className="flex flex-col gap-1">
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
        </aside>
      )}
      <div className="min-w-0 p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <button type="button" onClick={alternarMenu} className="rounded-full border border-[#f0e4e6] bg-white px-3 py-1.5 text-sm">
            {oculto ? "Mostrar menu" : "Ocultar menu"}
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
