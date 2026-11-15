"use client";

import { useEffect, useState } from "react";
import { PainelDoSalao } from "@/components/salao/PaineisSalao";
import { SalaoAPI, type PainelSalao } from "@/lib/salao-api";

export default function SalaoVisaoGeralPage() {
  const [painel, setPainel] = useState<PainelSalao | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    SalaoAPI.config().then((dados) => setPainel(dados.painel)).catch((exc: Error) => setErro(exc.message));
    function aoTrocar(evento: Event) {
      const proximo = (evento as CustomEvent<PainelSalao>).detail;
      if (proximo === "operacao" || proximo === "gestao" || proximo === "semana") setPainel(proximo);
    }
    window.addEventListener("salao-painel", aoTrocar);
    return () => window.removeEventListener("salao-painel", aoTrocar);
  }, []);

  if (erro) return <p className="text-sm text-red-700">{erro}</p>;
  if (!painel) return <p className="text-sm text-[#8a6e74]">Carregando o painel...</p>;
  return <PainelDoSalao painel={painel} />;
}
