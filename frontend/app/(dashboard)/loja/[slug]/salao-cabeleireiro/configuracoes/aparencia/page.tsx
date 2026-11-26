"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import apiClient from "@/lib/api-client";
import { AgendaV7Preview } from "@/components/shared/agenda/AgendaV7Preview";
import { hexCor, STATUS_PADRAO } from "@/components/salao/cores-salao";
import { normalizeAgendaVisual, type AgendaVisualId } from "@/lib/shared/agenda/visual";

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
  agenda_visual?: string | null;
};

function amostrasDoSalao(cores: Record<string, { bg?: string; border?: string }>) {
  const hoje = new Date();
  const dia = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, "0")}-${String(hoje.getDate()).padStart(2, "0")}`;
  const cor = (status: string) => cores[status] || { bg: STATUS_PADRAO[status] || "#7a3044", border: STATUS_PADRAO[status] || "#7a3044" };
  const item = (id: string, inicio: string, fim: string, cliente: string, status: string, profissional: number, profissionalNome: string, servico: string) => {
    const tinta = cor(status);
    return {
      id,
      title: cliente,
      start: `${dia}T${inicio}`,
      end: `${dia}T${fim}`,
      color: tinta.bg,
      contrastColor: "#fff",
      backgroundColor: tinta.bg,
      borderColor: tinta.border,
      extendedProps: { status, patient_name: cliente, professional: profissional, professional_name: profissionalNome, procedure_name: servico },
    };
  };
  return [
    item("corte", "09:00:00", "09:45:00", "Helena Prado", "SCHEDULED", 1, "Lia Costa", "Corte"),
    item("barba", "10:00:00", "10:30:00", "Caio Mendes", "CONFIRMED", 2, "Rafael Nunes", "Barba"),
    item("escova", "11:00:00", "11:45:00", "Marina Luz", "IN_PROGRESS", 1, "Lia Costa", "Escova"),
    item("cor", "14:00:00", "16:00:00", "Pedro Alves", "COMPLETED", 2, "Rafael Nunes", "Coloração"),
    {
      id: "intervalo",
      title: "Intervalo",
      start: `${dia}T12:00:00`,
      end: `${dia}T13:00:00`,
      color: "#f4d7b0",
      contrastColor: "#7a4b12",
      backgroundColor: "#f4d7b0",
      borderColor: "#e8b86a",
      extendedProps: { isBloqueio: true, motivo: "Intervalo", professional: 1, professional_name: "Lia Costa" },
    },
  ];
}

export default function AparenciaSalaoPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const [form, setForm] = useState<Identidade | null>(null);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [visual, setVisual] = useState<AgendaVisualId>("pulse");

  useEffect(() => {
    apiClient.get<Identidade>("/salao-cabeleireiro/identidade/").then((resposta) => {
      const id = normalizeAgendaVisual(resposta.data.agenda_visual);
      setForm(normalizar(resposta.data));
      setVisual(id);
      lembrarVisual(slug, id);
    }).catch(() => setErro("Não foi possível carregar a identidade visual."));
  }, [slug]);

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
      agenda_visual: visual,
    };
    try {
      const resposta = await apiClient.patch<Identidade>("/salao-cabeleireiro/identidade/", corpo);
      const gravado = normalizar(resposta.data);
      setForm(gravado);
      lembrarVisual(slug, visual);
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
      <p className="mt-1 text-sm text-[#8a6e74]">Cor do menu, fundo das páginas, cores dos status e o visual da agenda. O tema vale para Dia, Semana e Mês.</p>
      {erro ? <p className="mt-3 text-sm text-red-700">{erro}</p> : null}
      {aviso ? <p className="mt-3 text-sm text-[#1f8a4c]">{aviso}</p> : null}
      {form ? (
        <div className="mt-4 grid items-start gap-4 xl:grid-cols-[20rem_minmax(0,1fr)]">
          <section className="space-y-4 rounded-3xl border border-[#f0e4e6] bg-white p-4">
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
          </section>
          <section className="min-w-0 rounded-3xl border border-[#f0e4e6] bg-white p-4">
            <AgendaV7Preview
              statusColors={form.agenda_status_colors}
              accentColor={form.cor_primaria}
              value={visual}
              iniciarAberta
              altura={720}
              construirAmostras={amostrasDoSalao}
            onChange={(id) => {
              setVisual(id);
              lembrarVisual(slug, id);
              apiClient.patch("/salao-cabeleireiro/identidade/", { agenda_visual: id }).then(() => setAviso("O visual da agenda ficou gravado neste salão.")).catch(() => setErro("Não foi possível gravar o visual da agenda."));
            }}
            />
          </section>
        </div>
      ) : null}
    </div>
  );
}

function lembrarVisual(slug: string, id: AgendaVisualId) {
  try { window.sessionStorage.setItem(`lwk:salao-agenda-visual:${slug}`, id); } catch { /* o navegador pode bloquear a sessão */ }
  window.dispatchEvent(new CustomEvent("salao-agenda-visual", { detail: id }));
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
