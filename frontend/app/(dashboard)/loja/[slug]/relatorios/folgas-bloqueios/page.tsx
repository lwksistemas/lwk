"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Download, Search } from "lucide-react";
import { clinicaBelezaFetch, ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import {
  ClinicaBelezaPageContent,
  ClinicaBelezaPanel,
} from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { RelatorioPdfActions } from "@/components/clinica-beleza/relatorios-shared/RelatorioPdfActions";
import { abrirRelatorioPdf } from "@/components/clinica-beleza/relatorios-shared/abrir-relatorio-pdf";

type Evento = {
  id: number;
  ids?: number[];
  tipo: string;
  tipo_label: string;
  titulo: string;
  data_inicio: string | null;
  data_fim: string | null;
  horario_inicio: string | null;
  horario_fim: string | null;
  dia_inteiro: boolean;
  observacoes: string;
  dias_no_periodo: number;
  profissional_id: number | null;
  profissional_nome: string;
};

function chaveEvento(ev: Evento): string {
  if (ev.ids?.length) return ev.ids.join("-");
  return String(ev.id);
}

type ProfissionalLinha = {
  professional_id: number;
  nome: string;
  dias_semana_trabalho: string[];
  dias_escala: number;
  dias_trabalhados: number;
  dias_folga: number;
  dias_bloqueio: number;
  eventos: Evento[];
};

type RelatorioData = {
  data_inicio: string;
  data_fim: string;
  profissionais: ProfissionalLinha[];
  bloqueios_gerais: Evento[];
  totais: {
    profissionais: number;
    dias_escala: number;
    dias_trabalhados: number;
    dias_folga: number;
    dias_bloqueio: number;
    bloqueios_gerais: number;
  };
};

function formatDate(iso: string | null) {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

export default function FolgasBloqueiosRelatorioPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [dataInicio, setDataInicio] = useState(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split("T")[0];
  });
  const [dataFim, setDataFim] = useState(() => new Date().toISOString().split("T")[0]);
  const [professionalId, setProfessionalId] = useState("");
  const [profissionaisOpts, setProfissionaisOpts] = useState<Array<{ id: number; nome: string }>>([]);
  const [data, setData] = useState<RelatorioData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void ClinicaBelezaAPI.professionals
      .list({ active: true, all: true })
      .then((lista) => {
        const rows = Array.isArray(lista) ? lista : [];
        setProfissionaisOpts(
          rows
            .map((p) => ({ id: p.id, nome: p.nome }))
            .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")),
        );
      })
      .catch(() => setProfissionaisOpts([]));
  }, []);

  const buscar = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
      if (professionalId) qp.set("professional_id", professionalId);
      const res = await clinicaBelezaFetch(`/relatorios/folgas-bloqueios/?${qp.toString()}`);
      if (res.ok) {
        setData(await res.json());
      } else {
        setError("Erro ao carregar dados. Tente novamente.");
        setData(null);
      }
    } catch {
      setError("Erro ao carregar dados. Tente novamente.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [dataInicio, dataFim, professionalId]);

  useEffect(() => {
    void buscar();
  }, [buscar]);

  const exportarCSV = () => {
    if (!data) return;
    const BOM = "\ufeff";
    let csv =
      "Profissional;Escala;Trabalhados;Folga;Bloqueio;Dias da semana;Tipo;Título;Início;Fim;Horário;Dias no período\n";
    for (const p of data.profissionais) {
      if (!p.eventos.length) {
        csv += `${p.nome};${p.dias_escala};${p.dias_trabalhados};${p.dias_folga};${p.dias_bloqueio};${(p.dias_semana_trabalho || []).join(" ")};\n`;
        continue;
      }
      for (const ev of p.eventos) {
        const horario = ev.dia_inteiro
          ? "Dia inteiro"
          : `${ev.horario_inicio || ""}-${ev.horario_fim || ""}`;
        csv +=
          `${p.nome};${p.dias_escala};${p.dias_trabalhados};${p.dias_folga};${p.dias_bloqueio};` +
          `${(p.dias_semana_trabalho || []).join(" ")};${ev.tipo_label};${ev.titulo};` +
          `${formatDate(ev.data_inicio)};${formatDate(ev.data_fim)};${horario};${ev.dias_no_periodo}\n`;
      }
    }
    for (const ev of data.bloqueios_gerais) {
      const horario = ev.dia_inteiro
        ? "Dia inteiro"
        : `${ev.horario_inicio || ""}-${ev.horario_fim || ""}`;
      csv +=
        `Todos;;;;;;${ev.tipo_label};${ev.titulo};${formatDate(ev.data_inicio)};` +
        `${formatDate(ev.data_fim)};${horario};${ev.dias_no_periodo}\n`;
    }
    const blob = new Blob([BOM + csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `folgas_bloqueios_${dataInicio}_${dataFim}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const abrirPdf = (modo: "visualizar" | "imprimir", janela: Window | null) => {
    const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
    if (professionalId) qp.set("professional_id", professionalId);
    return abrirRelatorioPdf(`/relatorios/folgas-bloqueios/pdf/?${qp.toString()}`, modo, janela);
  };

  const temDados =
    Boolean(data?.profissionais.length) || Boolean(data?.bloqueios_gerais.length);

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Folgas, bloqueios e dias trabalhados"
        subtitle={`Período: ${dataInicio} a ${dataFim}`}
        backHref={`/loja/${slug}/relatorios`}
        extraActions={
          <>
            <button
              type="button"
              onClick={exportarCSV}
              disabled={!temDados}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 disabled:opacity-50"
            >
              <Download size={16} />
              <span className="hidden sm:inline">CSV</span>
            </button>
            <RelatorioPdfActions disabled={!temDados} onPdf={abrirPdf} />
          </>
        }
      />
      <ClinicaBelezaPageContent>
        <ClinicaBelezaPanel className="p-4 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data início
              </label>
              <input
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data fim
              </label>
              <input
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Profissional
              </label>
              <select
                value={professionalId}
                onChange={(e) => setProfessionalId(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              >
                <option value="">Todos</option>
                {profissionaisOpts.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              onClick={() => void buscar()}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white disabled:opacity-60"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              <Search size={16} />
              {loading ? "Buscando…" : "Buscar"}
            </button>
          </div>
          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
        </ClinicaBelezaPanel>

        {data ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
            {[
              { label: "Escala (dias)", value: data.totais.dias_escala },
              { label: "Trabalhados", value: data.totais.dias_trabalhados },
              { label: "Folga / férias", value: data.totais.dias_folga },
              { label: "Outros bloqueios", value: data.totais.dias_bloqueio },
            ].map((c) => (
              <div
                key={c.label}
                className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3"
              >
                <p className="text-xs text-gray-500 dark:text-gray-400">{c.label}</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white mt-0.5">{c.value}</p>
              </div>
            ))}
          </div>
        ) : null}

        {loading && !data ? (
          <p className="text-sm text-gray-500">Carregando…</p>
        ) : !temDados ? (
          <ClinicaBelezaPanel className="p-6 text-sm text-gray-500">
            Nenhum profissional ou bloqueio no período.
          </ClinicaBelezaPanel>
        ) : (
          <div className="space-y-4">
            {data?.profissionais.map((p) => (
              <ClinicaBelezaPanel key={p.professional_id} className="overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">{p.nome}</p>
                    <p className="text-xs text-gray-500">
                      Semana: {(p.dias_semana_trabalho || []).join(", ") || "—"}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-3 text-xs text-gray-600 dark:text-gray-300">
                    <span>Escala {p.dias_escala}</span>
                    <span>Trabalhados {p.dias_trabalhados}</span>
                    <span>Folga {p.dias_folga}</span>
                    <span>Bloqueio {p.dias_bloqueio}</span>
                  </div>
                </div>
                {p.eventos.length === 0 ? (
                  <p className="px-4 py-3 text-xs text-gray-500">Sem folga/bloqueio individual no período.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="text-left text-gray-500 border-b border-gray-100 dark:border-gray-700">
                          <th className="px-4 py-2 font-medium">Tipo</th>
                          <th className="px-4 py-2 font-medium">Título</th>
                          <th className="px-4 py-2 font-medium">Período</th>
                          <th className="px-4 py-2 font-medium">Horário</th>
                          <th className="px-4 py-2 font-medium">Dias</th>
                        </tr>
                      </thead>
                      <tbody>
                        {p.eventos.map((ev) => (
                          <tr
                            key={chaveEvento(ev)}
                            className="border-b border-gray-50 dark:border-gray-800 last:border-0"
                          >
                            <td className="px-4 py-2">{ev.tipo_label}</td>
                            <td className="px-4 py-2">{ev.titulo}</td>
                            <td className="px-4 py-2">
                              {formatDate(ev.data_inicio)}
                              {ev.data_fim && ev.data_fim !== ev.data_inicio
                                ? ` a ${formatDate(ev.data_fim)}`
                                : ""}
                            </td>
                            <td className="px-4 py-2">
                              {ev.dia_inteiro
                                ? "Dia inteiro"
                                : `${ev.horario_inicio || ""}–${ev.horario_fim || ""}`}
                            </td>
                            <td className="px-4 py-2">{ev.dias_no_periodo}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </ClinicaBelezaPanel>
            ))}

            {data && data.bloqueios_gerais.length > 0 ? (
              <ClinicaBelezaPanel className="overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">
                    Bloqueios gerais (todos os profissionais)
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-left text-gray-500 border-b border-gray-100 dark:border-gray-700">
                        <th className="px-4 py-2 font-medium">Tipo</th>
                        <th className="px-4 py-2 font-medium">Título</th>
                        <th className="px-4 py-2 font-medium">Período</th>
                        <th className="px-4 py-2 font-medium">Horário</th>
                        <th className="px-4 py-2 font-medium">Dias</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.bloqueios_gerais.map((ev) => (
                        <tr
                          key={`g-${chaveEvento(ev)}`}
                          className="border-b border-gray-50 dark:border-gray-800 last:border-0"
                        >
                          <td className="px-4 py-2">{ev.tipo_label}</td>
                          <td className="px-4 py-2">{ev.titulo}</td>
                          <td className="px-4 py-2">
                            {formatDate(ev.data_inicio)}
                            {ev.data_fim && ev.data_fim !== ev.data_inicio
                              ? ` a ${formatDate(ev.data_fim)}`
                              : ""}
                          </td>
                          <td className="px-4 py-2">
                            {ev.dia_inteiro
                              ? "Dia inteiro"
                              : `${ev.horario_inicio || ""}–${ev.horario_fim || ""}`}
                          </td>
                          <td className="px-4 py-2">{ev.dias_no_periodo}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </ClinicaBelezaPanel>
            ) : null}
          </div>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
