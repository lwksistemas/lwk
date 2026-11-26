"use client";

import { useEffect, useMemo, useState } from "react";
import { celulasCalendarioMes, tituloMesCalendario } from "@/lib/shared/agenda/agenda-dia-colunas-utils";

const DIAS = ["D", "S", "T", "Q", "Q", "S", "S"];
const CHAVE = "salao-agenda-ocultar-lateral";

export function useSalaoLateral() {
  const [ocultar, setOcultar] = useState(false);
  const [pronto, setPronto] = useState(false);

  useEffect(() => {
    try {
      setOcultar(window.localStorage.getItem(CHAVE) === "1");
    } catch { /* o navegador pode bloquear a sessão */ }
    setPronto(true);
  }, []);

  useEffect(() => {
    if (!pronto) return;
    try {
      window.localStorage.setItem(CHAVE, ocultar ? "1" : "0");
    } catch { /* o navegador pode bloquear a sessão */ }
  }, [ocultar, pronto]);

  return { ocultar, setOcultar };
}

export function SalaoAgendaLateral({
  diaIso,
  hojeIso,
  itens,
  aoEscolherDia,
  aoAbrir,
  expandir = false,
}: {
  diaIso: string;
  hojeIso: string;
  itens: { chave: string; hora: string; cliente: string; detalhe: string; status: string; cor: string }[];
  aoEscolherDia: (iso: string) => void;
  aoAbrir: (chave: string) => void;
  expandir?: boolean;
}) {
  const celulas = useMemo(() => celulasCalendarioMes(diaIso), [diaIso]);
  const titulo = tituloMesCalendario(diaIso);

  return (
    <aside className={`hidden min-h-0 flex-col border-l border-[#f0e4e6] bg-white lg:flex ${expandir ? "min-w-64 flex-1" : "w-64 shrink-0"}`}>
      <div className="shrink-0 p-4 pb-3">
        <p className="mb-3 text-sm font-semibold text-[#2a1c20] capitalize">{titulo}</p>
        <div className="grid grid-cols-7 gap-y-1 text-center">
          {DIAS.map((dia, indice) => <span key={`${dia}-${indice}`} className="py-1 text-[10px] font-medium text-[#8a6e74]">{dia}</span>)}
          {celulas.map((celula) => {
            const escolhido = celula.iso === diaIso;
            const hoje = celula.iso === hojeIso;
            return (
              <button
                key={celula.iso}
                type="button"
                onClick={() => aoEscolherDia(celula.iso)}
                className={`h-8 rounded-full text-xs ${escolhido ? "font-semibold text-white" : hoje ? "font-semibold text-[#2a1c20]" : celula.inMonth ? "text-[#5c3d45] hover:bg-[#f7f2f4]" : "text-[#d7c4c8]"}`}
                style={escolhido ? { background: "var(--agenda-accent, #7a3044)" } : undefined}
              >
                {Number(celula.iso.slice(-2))}
              </button>
            );
          })}
        </div>
      </div>
      <div className="flex min-h-0 flex-1 flex-col border-t border-[#f0e4e6]">
        <div className="flex items-baseline justify-between px-4 pt-3 pb-1.5">
          <h3 className="text-sm font-semibold text-[#2a1c20]">Neste dia</h3>
          <span className="text-[11px] text-[#8a6e74]">{itens.length}</span>
        </div>
        {itens.length === 0 ? <p className="px-4 py-3 text-xs text-[#8a6e74]">Nenhum agendamento neste dia.</p> : (
          <ul className="min-h-0 flex-1 space-y-1 overflow-y-auto px-2 pb-3">
            {itens.map((item) => (
              <li key={item.chave}>
                <button type="button" className="w-full rounded-lg px-2 py-1.5 text-left hover:bg-[#f7f2f4]" style={{ borderLeft: `3px solid ${item.cor}` }} onClick={() => aoAbrir(item.chave)}>
                  <span className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-semibold text-[#5c3d45]">{item.hora}</span>
                    <span className="max-w-[6rem] truncate rounded-full px-1.5 py-0.5 text-[10px] font-semibold text-white" style={{ background: item.cor }}>{item.status}</span>
                  </span>
                  <span className="mt-0.5 block truncate text-xs font-semibold text-[#2a1c20]">{item.cliente}</span>
                  <span className="block truncate text-[11px] text-[#8a6e74]">{item.detalhe}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
