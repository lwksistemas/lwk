"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { FileUp, FlaskConical, Loader2, Trash2 } from "lucide-react";
import { ConsultaPrintButton } from "@/components/clinica-beleza/consultas/ConsultaPrintButton";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api/client";
import {
  abrirPdfBlobFromResponse,
  fecharJanelaPdf,
  type ConsultaPdfModo,
} from "@/lib/consulta-print";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";

type PedidoPendente = {
  tipo: "documento" | "memed";
  id: number;
  consulta_id: number;
  titulo: string;
  quando: string | null;
};

type Marcador = {
  codigo: string;
  nome: string;
  valor: number;
  unidade: string;
  faixa_min: number | null;
  faixa_max: number | null;
  origem_faixa: string;
  status: string;
};

type Resultado = {
  id: number;
  pdf_url: string;
  nome_arquivo: string;
  marcadores: Marcador[];
  sugestao_texto: string;
  aviso_cadastro: string;
  created_at: string | null;
  documento_origem_id: number | null;
  prescricao_origem_id: number | null;
};

function corStatus(status: string) {
  if (status === "alto" || status === "baixo") return "text-amber-700 dark:text-amber-300";
  if (status === "dentro") return "text-emerald-700 dark:text-emerald-300";
  return "text-gray-500";
}

function rotuloStatus(status: string) {
  if (status === "alto") return "Acima";
  if (status === "baixo") return "Abaixo";
  if (status === "dentro") return "Dentro da faixa";
  return "Sem referência";
}

export function ResultadoExameSection({
  consultaId,
  consultaAtiva,
}: {
  consultaId: number;
  consultaAtiva: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");
  const [podeImportar, setPodeImportar] = useState(false);
  const [pedidos, setPedidos] = useState<PedidoPendente[]>([]);
  const [resultados, setResultados] = useState<Resultado[]>([]);
  const [pedidoEscolhido, setPedidoEscolhido] = useState<string>("");
  const [perfilAviso, setPerfilAviso] = useState("");

  const imprimirAnalise = async (
    resultadoId: number,
    _modo: ConsultaPdfModo,
    janela?: Window | null,
  ) => {
    const path = ClinicaBelezaAPI.consultas.resultadosExame.pdfUrl(consultaId, resultadoId);
    const response = await clinicaBelezaFetch(path);
    if (!response.ok) {
      fecharJanelaPdf(janela ?? null);
      throw new Error("Não foi possível gerar o PDF da análise.");
    }
    await abrirPdfBlobFromResponse(response, "visualizar", janela);
  };

  const carregar = useCallback(async () => {
    setLoading(true);
    setErro("");
    try {
      const data = await ClinicaBelezaAPI.consultas.resultadosExame.list(consultaId);
      setPodeImportar(Boolean(data.pode_importar));
      setPedidos(data.pedidos_pendentes || []);
      setResultados((data.resultados || []) as Resultado[]);
      setPerfilAviso(data.perfil?.aviso || "");
      setPedidoEscolhido((atual) => {
        if (atual) return atual;
        const primeiro = data.pedidos_pendentes?.[0];
        return primeiro ? `${primeiro.tipo}:${primeiro.id}` : "";
      });
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível carregar os resultados.");
    } finally {
      setLoading(false);
    }
  }, [consultaId]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  async function enviarArquivo(file: File) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setErro("Envie um arquivo PDF.");
      return;
    }
    setEnviando(true);
    setErro("");
    try {
      const extras: {
        documento_origem_id?: number;
        prescricao_origem_id?: number;
        consulta_origem_id?: number;
      } = {};
      const ped = pedidos.find((p) => `${p.tipo}:${p.id}` === pedidoEscolhido);
      if (ped?.tipo === "documento") {
        extras.documento_origem_id = ped.id;
        extras.consulta_origem_id = ped.consulta_id;
      } else if (ped?.tipo === "memed") {
        extras.prescricao_origem_id = ped.id;
        extras.consulta_origem_id = ped.consulta_id;
      }
      await ClinicaBelezaAPI.consultas.resultadosExame.importar(consultaId, file, extras);
      setPedidoEscolhido("");
      await carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível importar o PDF.");
    } finally {
      setEnviando(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function excluir(id: number) {
    setErro("");
    try {
      await ClinicaBelezaAPI.consultas.resultadosExame.excluir(consultaId, id);
      await carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível excluir.");
    }
  }

  if (loading) {
    return (
      <div className="rounded-2xl border border-gray-200 dark:border-gray-700 p-4 text-sm text-gray-500 flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" /> Carregando resultados de exame…
      </div>
    );
  }

  if (!podeImportar && resultados.length === 0) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-violet-100 dark:border-violet-900/40 bg-violet-50/40 dark:bg-violet-950/20 p-4 space-y-3">
      <div className="flex items-start gap-2">
        <FlaskConical className="h-5 w-5 text-violet-700 dark:text-violet-300 mt-0.5 shrink-0" />
        <div>
          <h3 className="text-sm font-semibold text-violet-900 dark:text-violet-100">Resultado de exame</h3>
          <p className="text-xs text-violet-800/80 dark:text-violet-200/70 mt-0.5">
            Se houve pedido de exame em consulta anterior, importe o PDF do laboratório. A sugestão usa a faixa do laudo
            ou o catálogo interno conforme sexo e idade do cadastro — não substitui a avaliação profissional.
          </p>
        </div>
      </div>

      {perfilAviso ? <p className="text-xs text-amber-700 dark:text-amber-300">{perfilAviso}</p> : null}
      {erro ? <p className="text-xs text-red-600">{erro}</p> : null}

      {podeImportar && consultaAtiva ? (
        <div className="space-y-2 rounded-xl bg-white/80 dark:bg-gray-900/40 p-3">
          {pedidos.length > 0 ? (
            <label className="block text-xs text-gray-600 dark:text-gray-300">
              Pedido de exame
              <select
                className="mt-1 w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-2 py-1.5 text-sm"
                value={pedidoEscolhido}
                onChange={(e) => setPedidoEscolhido(e.target.value)}
              >
                {pedidos.map((p) => (
                  <option key={`${p.tipo}-${p.id}`} value={`${p.tipo}:${p.id}`}>
                    {p.titulo} · consulta #{p.consulta_id}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <div className="flex flex-wrap items-center gap-2">
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void enviarArquivo(file);
              }}
            />
            <button
              type="button"
              disabled={enviando}
              onClick={() => inputRef.current?.click()}
              className="inline-flex items-center gap-2 rounded-xl bg-violet-700 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
            >
              {enviando ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
              Importar PDF do resultado
            </button>
          </div>
        </div>
      ) : null}

      {resultados.length === 0 ? (
        <p className="text-xs text-gray-500">Nenhum resultado importado ainda para este paciente.</p>
      ) : (
        <ul className="space-y-3">
          {resultados.map((r) => (
            <li key={r.id} className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-3 space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <a
                    href={r.pdf_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-medium text-violet-700 dark:text-violet-300 truncate block"
                  >
                    {r.nome_arquivo || "Resultado.pdf"}
                  </a>
                  {r.created_at ? (
                    <p className="text-[11px] text-gray-500">
                      {new Date(r.created_at).toLocaleString("pt-BR")}
                    </p>
                  ) : null}
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <ConsultaPrintButton
                    labelVisualizar="PDF análise"
                    onAction={(modo, janela) => imprimirAnalise(r.id, modo, janela)}
                  />
                  {consultaAtiva ? (
                    <button
                      type="button"
                      aria-label="Excluir resultado"
                      className="rounded-lg p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600"
                      onClick={() => void excluir(r.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  ) : null}
                </div>
              </div>
              <p className="text-[11px] text-gray-500 dark:text-gray-400">
                A sugestão usa a faixa do laudo ou o catálogo interno conforme sexo e idade do
                cadastro — não substitui a avaliação profissional.
              </p>
              {r.aviso_cadastro ? <p className="text-[11px] text-amber-700">{r.aviso_cadastro}</p> : null}
              {r.marcadores?.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-left text-gray-500">
                        <th className="py-1 pr-2 font-medium">Exame</th>
                        <th className="py-1 pr-2 font-medium">Valor</th>
                        <th className="py-1 pr-2 font-medium">Referência</th>
                        <th className="py-1 font-medium">Sugestão</th>
                      </tr>
                    </thead>
                    <tbody>
                      {r.marcadores.map((m, idx) => (
                        <tr key={`${m.codigo}-${idx}`} className="border-t border-gray-100 dark:border-gray-800">
                          <td className="py-1 pr-2">{m.nome}</td>
                          <td className="py-1 pr-2 tabular-nums">
                            {m.valor} {m.unidade}
                          </td>
                          <td className="py-1 pr-2 tabular-nums text-gray-500">
                            {m.faixa_min != null || m.faixa_max != null
                              ? `${m.faixa_min ?? "…"} – ${m.faixa_max ?? "…"}`
                              : "—"}
                          </td>
                          <td className={`py-1 font-medium ${corStatus(m.status)}`}>{rotuloStatus(m.status)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-xs text-gray-500">
                  Nenhum biomarcador reconhecido automaticamente. Abra o PDF e avalie o laudo.
                </p>
              )}
              {r.sugestao_texto ? (
                <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 dark:bg-gray-800/60 p-2 text-[11px] text-gray-700 dark:text-gray-200">
                  {r.sugestao_texto}
                </pre>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
