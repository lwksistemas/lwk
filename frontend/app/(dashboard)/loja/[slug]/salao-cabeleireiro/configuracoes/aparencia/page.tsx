"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import apiClient from "@/lib/api-client";
import { hexCor, STATUS_PADRAO } from "@/components/salao/cores-salao";

const STATUS = [
  ["SCHEDULED", "Aguardando"],
  ["CONFIRMED", "Confirmado"],
  ["IN_PROGRESS", "Em atendimento"],
  ["COMPLETED", "Concluído"],
  ["CANCELLED", "Cancelado"],
  ["NO_SHOW", "Faltou"],
] as const;

type Identidade = {
  cor_primaria: string;
  cor_secundaria: string;
  cor_fundo_pagina: string;
  agenda_status_colors: Record<string, { bg?: string; border?: string }>;
};

export default function AparenciaSalaoPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const [form, setForm] = useState<Identidade | null>(null);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");

  useEffect(() => {
    apiClient.get<Identidade>("/salao-cabeleireiro/identidade/").then((resposta) => setForm(normalizar(resposta.data))).catch(() => setErro("Não foi possível carregar a identidade visual."));
  }, []);

  async function gravar() {
    if (!form) return;
    setErro("");
    setAviso("");
    const mapa = form.agenda_status_colors || {};
    const cores = Object.fromEntries(STATUS.map(([codigo]) => {
      const atual = hexCor(mapa[codigo]?.bg, STATUS_PADRAO[codigo]);
      return [codigo, { bg: atual, border: atual }];
    }));
    const corpo = {
      cor_primaria: hexCor(form.cor_primaria, "#7a3044"),
      cor_secundaria: hexCor(form.cor_secundaria, "#4c1d78"),
      cor_fundo_pagina: hexCor(form.cor_fundo_pagina, "#fbf6f4"),
      agenda_status_colors: cores,
    };
    try {
      const resposta = await apiClient.patch<Identidade>("/salao-cabeleireiro/identidade/", corpo);
      const gravado = normalizar(resposta.data);
      setForm(gravado);
      window.dispatchEvent(new CustomEvent("salao-identidade", { detail: gravado }));
      setAviso("A identidade visual ficou gravada neste salão.");
    } catch (exc) {
      const resposta = (exc as { response?: { data?: { error?: string } } }).response?.data?.error;
      setErro(typeof resposta === "string" ? resposta : "Não foi possível gravar as cores.");
    }
  }

  return (
    <div>
      <Link href={`/loja/${slug}/salao-cabeleireiro/configuracoes`} className="mb-4 inline-flex items-center gap-2 text-sm text-[#8a6e74]">
        <ArrowLeft size={16} /> Voltar às configurações
      </Link>
      <h1 className="text-2xl font-semibold">Identidade visual</h1>
      <p className="mt-1 max-w-2xl text-sm text-[#8a6e74]">Cor do menu, fundo das páginas e cores dos status da agenda. O layout do dashboard continua o que o administrador escolheu.</p>
      {erro ? <p className="mt-3 text-sm text-red-700">{erro}</p> : null}
      {aviso ? <p className="mt-3 text-sm text-[#1f8a4c]">{aviso}</p> : null}
      {form ? (
        <div className="mt-4 max-w-xl space-y-4 rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <Cor nome="Cor do menu" valor={form.cor_primaria} aoMudar={(valor) => setForm({ ...form, cor_primaria: valor })} />
          <Cor nome="Cor secundária" valor={form.cor_secundaria} aoMudar={(valor) => setForm({ ...form, cor_secundaria: valor })} />
          <Cor nome="Fundo das páginas" valor={form.cor_fundo_pagina} aoMudar={(valor) => setForm({ ...form, cor_fundo_pagina: valor })} />
          <div className="grid gap-2">
            {STATUS.map(([codigo, nome]) => (
              <Cor
                key={codigo}
                nome={nome}
                valor={hexCor(form.agenda_status_colors?.[codigo]?.bg, STATUS_PADRAO[codigo])}
                aoMudar={(valor) => setForm({ ...form, agenda_status_colors: { ...form.agenda_status_colors, [codigo]: { bg: valor, border: valor } } })}
              />
            ))}
          </div>
          <button type="button" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" onClick={gravar}>Gravar identidade</button>
        </div>
      ) : null}
    </div>
  );
}

function normalizar(dados: Identidade): Identidade {
  const mapa = dados.agenda_status_colors || {};
  return {
    cor_primaria: hexCor(dados.cor_primaria, "#7a3044"),
    cor_secundaria: hexCor(dados.cor_secundaria, "#4c1d78"),
    cor_fundo_pagina: hexCor(dados.cor_fundo_pagina, "#fbf6f4"),
    agenda_status_colors: Object.fromEntries(STATUS.map(([codigo]) => {
      const cor = hexCor(mapa[codigo]?.bg, STATUS_PADRAO[codigo]);
      return [codigo, { bg: cor, border: cor }];
    })),
  };
}

function Cor({ nome, valor, aoMudar }: { nome: string; valor: string; aoMudar: (valor: string) => void }) {
  const hex = hexCor(valor, "#7a3044");
  return (
    <label className="flex items-center justify-between gap-3 text-sm">
      {nome}
      <input type="color" value={hex} aria-label={nome} onChange={(evento) => aoMudar(hexCor(evento.target.value, hex))} />
    </label>
  );
}
