"use client";

import { useEffect, useState } from "react";
import { Check, Columns2, Trash2, X } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ClinicaBelezaAPI, type PacienteFotoItem } from "@/lib/clinica-beleza-api";
import {
  simulacaoEsteticaApi,
  type SimulacaoEsteticaConfig,
} from "@/lib/clinica-beleza-api/client-ops";
import type { SimulacaoConsultaItem } from "@/lib/clinica-beleza-api/client-consultas";
import type { ConsultaDetailTabPanelsProps } from "./tab-panels-types";

const NOTAS: Record<string, string> = {
  pore: "Poros",
  texture: "Textura",
  wrinkle: "Rugas",
  acne: "Acne",
  skin_age: "Idade da pele",
};

const MODOS = [
  { id: "analise", rotulo: "Analisar a pele" },
  { id: "pele", rotulo: "Simular a pele" },
  { id: "rosto", rotulo: "Simular o rosto" },
  { id: "corpo", rotulo: "Simular o corpo" },
] as const;

const AVISO = "Simulação ilustrativa. Não é previsão de uma dose e não substitui o termo de consentimento.";

const ENDPOINTS: Record<string, string> = {
  analise: "POST /s2s/v2.0/task/skin-analysis",
  pele: "POST /s2s/v2.0/task/skin-simulation",
  rosto: "POST /s2s/v2.0/task/face-reshape",
  corpo: "POST /s2s/v2.0/task/body-reshape",
};

const SENTIDO: Record<string, { negativo: string; positivo: string }> = {
  lip_size: { negativo: "lábios menores", positivo: "lábios maiores" },
  nose_size: { negativo: "nariz menor", positivo: "nariz maior" },
  chin_length: { negativo: "queixo mais curto", positivo: "queixo mais longo" },
  eye_size: { negativo: "olhos menores", positivo: "olhos maiores" },
  waist: { negativo: "cintura mais estreita", positivo: "cintura mais larga" },
  belly: { negativo: "abdômen mais plano", positivo: "abdômen mais projetado" },
  hip: { negativo: "quadril mais estreito", positivo: "quadril mais largo" },
};

function rotuloParametro(modo: string, parametro: string): string {
  return OPCOES[modo]?.find((opcao) => opcao.id === parametro)?.rotulo || "";
}

function textoIntensidade(modo: string, parametro: string, valor: number): string {
  const nome = rotuloParametro(modo, parametro);
  if (modo === "pele") {
    const faixa = valor <= 0.3 ? "sutil" : valor <= 0.6 ? "perceptível" : "mais forte";
    return `Intensidade visual ${valor.toFixed(1).replace(".", ",")} de 1,0 em ${nome} (${faixa}). Não é dose de produto.`;
  }
  const sentido = SENTIDO[parametro];
  const efeito = valor < 0 ? sentido?.negativo : valor > 0 ? sentido?.positivo : "sem ajuste";
  return `Intensidade visual ${valor} na escala de −100 a 100 (${efeito}). Não é dose de produto.`;
}

function avisoProcedimento(nome: string, modo: string): string {
  const texto = nome.toLowerCase();
  const facial = /facial|rosto|pele|testa|l[aá]bio|microagulh|botox|preenchimento/.test(texto);
  const corporal = /corporal|abd[oô]men|cintura|quadril|gl[uú]teo/.test(texto);
  if (facial && modo === "corpo") {
    return `O procedimento da agenda é ${nome}. Simular o corpo não corresponde a esse procedimento.`;
  }
  if (corporal && (modo === "pele" || modo === "rosto")) {
    return `O procedimento da agenda é ${nome}. Esta simulação é de rosto e não corresponde a esse procedimento.`;
  }
  return "";
}

function dataCurta(iso: string): string {
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return "";
  return data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

const OPCOES: Record<string, { id: string; rotulo: string }[]> = {
  pele: [
    { id: "wrinkle", rotulo: "Rugas" },
    { id: "pores", rotulo: "Poros" },
    { id: "redness", rotulo: "Vermelhidão" },
    { id: "spots", rotulo: "Manchas" },
    { id: "texture", rotulo: "Textura" },
  ],
  rosto: [
    { id: "lip_size", rotulo: "Lábios" },
    { id: "nose_size", rotulo: "Nariz" },
    { id: "chin_length", rotulo: "Queixo" },
    { id: "eye_size", rotulo: "Olhos" },
  ],
  corpo: [
    { id: "waist", rotulo: "Cintura" },
    { id: "belly", rotulo: "Abdômen" },
    { id: "hip", rotulo: "Quadril" },
  ],
};

function ComparacaoDual({
  original,
  gerada,
  excluindo,
  onExcluir,
  onClose,
}: {
  original: string;
  gerada: string;
  excluindo: boolean;
  onExcluir: () => void;
  onClose: () => void;
}) {
  const lados = [
    { url: original, legenda: "Original" },
    { url: gerada, legenda: "Gerada" },
  ];
  return (
    <div className="fixed inset-0 z-[210] bg-black" role="dialog" aria-modal>
      <div className="grid h-full grid-cols-1 md:grid-cols-2">
        {lados.map((lado) => (
          <div key={lado.legenda} className="relative h-full min-h-0 overflow-hidden">
            <img src={lado.url} alt={lado.legenda} className="h-full w-full object-cover" />
            <p className="absolute inset-x-0 top-0 bg-black/50 py-1 text-center text-xs text-white">{lado.legenda}</p>
          </div>
        ))}
      </div>
      <div className="absolute right-3 top-3 flex items-center gap-2">
        <button
          type="button"
          onClick={onExcluir}
          disabled={excluindo}
          className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60"
        >
          <Trash2 size={16} />
          {excluindo ? "Excluindo…" : "Excluir geração"}
        </button>
        <button type="button" onClick={onClose} className="rounded-lg bg-black/60 p-2 text-white hover:bg-black/80" aria-label="Fechar">
          <X size={22} />
        </button>
      </div>
      <p className="absolute inset-x-0 bottom-0 bg-black/80 px-4 py-2 text-center text-xs text-white">{AVISO}</p>
    </div>
  );
}

function mensagemErro(err: unknown): string {
  if (err && typeof err === "object" && "error" in err && typeof (err as { error?: unknown }).error === "string") {
    return (err as { error: string }).error;
  }
  return "Não foi possível gerar a simulação.";
}

export function SimulacaoTabPanel({ tab, selected, consultaAtiva }: ConsultaDetailTabPanelsProps) {
  const slug = (useParams()?.slug as string) ?? "";
  const [config, setConfig] = useState<SimulacaoEsteticaConfig | null>(null);
  const [fotos, setFotos] = useState<PacienteFotoItem[]>([]);
  const [resultados, setResultados] = useState<SimulacaoConsultaItem[]>([]);
  const [fotoId, setFotoId] = useState<number | null>(null);
  const [modo, setModo] = useState<(typeof MODOS)[number]["id"]>("analise");
  const [parametro, setParametro] = useState("wrinkle");
  const [intensidade, setIntensidade] = useState(30);
  const [quantidade, setQuantidade] = useState("");
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [marcadas, setMarcadas] = useState<Record<string, boolean>>({});
  const [dual, setDual] = useState<{ id: number; original: string; gerada: string } | null>(null);
  const [excluindoId, setExcluindoId] = useState<number | null>(null);

  useEffect(() => {
    if (tab !== "simulacao") return;
    let vivo = true;
    simulacaoEsteticaApi.config().then((dados) => vivo && setConfig(dados)).catch(() => vivo && setConfig(null));
    ClinicaBelezaAPI.consultas.fotos.list(selected.id).then((res) => vivo && setFotos(res.fotos || [])).catch(() => vivo && setFotos([]));
    return () => {
      vivo = false;
    };
  }, [tab, selected.id]);

  useEffect(() => {
    if (tab !== "simulacao") return;
    let vivo = true;
    const carregar = () => {
      ClinicaBelezaAPI.consultas.simulacao
        .list(selected.id)
        .then((res) => vivo && setResultados(res.resultados || []))
        .catch(() => undefined);
    };
    carregar();
    const timer = window.setInterval(carregar, 4000);
    return () => {
      vivo = false;
      window.clearInterval(timer);
    };
  }, [tab, selected.id, enviando]);

  useEffect(() => {
    const primeira = OPCOES[modo]?.[0]?.id;
    if (primeira) setParametro(primeira);
    setIntensidade(modo === "pele" ? 0.4 : 30);
  }, [modo]);

  async function excluirGeracao(itemId: number) {
    if (!window.confirm("Excluir esta geração? A foto original do paciente permanece.")) return;
    setExcluindoId(itemId);
    setErro("");
    try {
      await ClinicaBelezaAPI.consultas.simulacao.excluir(selected.id, itemId);
      setResultados((atual) => atual.filter((linha) => linha.id !== itemId));
      setMarcadas((atual) => {
        const proximo = { ...atual };
        delete proximo[`${itemId}:original`];
        delete proximo[`${itemId}:gerada`];
        return proximo;
      });
      setDual((atual) => (atual?.id === itemId ? null : atual));
    } catch (err) {
      setErro(mensagemErro(err));
    } finally {
      setExcluindoId(null);
    }
  }

  async function gerar() {
    if (!fotoId) {
      setErro("Toque na foto que será usada.");
      return;
    }
    setEnviando(true);
    setErro("");
    try {
      const criada = await ClinicaBelezaAPI.consultas.simulacao.criar(selected.id, {
        foto_id: fotoId,
        modo,
        parametro: modo === "analise" ? "" : parametro,
        intensidade: modo === "analise" ? 0 : intensidade,
        quantidade: quantidade === "" ? null : Number(quantidade),
      });
      if (criada.status === "erro") setErro(criada.erro || "Não foi possível gerar a simulação.");
    } catch (err) {
      setErro(mensagemErro(err));
    } finally {
      setEnviando(false);
    }
  }

  if (tab !== "simulacao") return null;
  const pronta = Boolean(config?.disponivel && config.ativa && config.chave_configurada);

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600 dark:text-gray-300">{AVISO} A quantidade planejada fica só no histórico e não baixa o estoque.</p>
      <p className="text-sm text-gray-600 dark:text-gray-300">
        Procedimento da agenda: {selected.procedure_name || "nenhum"}. A simulação não altera o agendamento nem o protocolo.
      </p>
      {!pronta && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          {config?.mensagem || "Ative a chave YouCam desta clínica para usar a simulação."}{" "}
          <Link href={`/loja/${slug}/clinica-beleza/configuracoes/simulacao`} className="underline">
            Abrir configurações
          </Link>
        </p>
      )}
      {pronta && consultaAtiva && (
        <div className="rounded-xl border border-gray-200 bg-white p-4 space-y-3 dark:border-gray-700 dark:bg-gray-800">
          <div>
            <p className="text-sm">Foto</p>
            {fotos.length === 0 ? (
              <p className="mt-1 text-sm text-gray-500">Nenhuma foto neste acompanhamento. Envie uma na aba Fotos.</p>
            ) : fotoId ? (
              <div className="mt-2 flex items-end gap-3">
                {fotos.filter((foto) => foto.id === fotoId).map((foto) => {
                  const legenda = `${foto.consulta_data || "—"} · ${foto.origem_display || "Foto"}`;
                  return (
                    <div key={foto.id} className="w-36 overflow-hidden rounded-xl border-2 border-[var(--cb-primary,#8B3D52)]">
                      <img src={foto.url} alt={legenda} className="aspect-square w-full object-cover" />
                      <span className="block bg-black/70 px-2 py-1 text-[10px] text-white">{legenda}</span>
                    </div>
                  );
                })}
                <button
                  type="button"
                  onClick={() => setFotoId(null)}
                  className="mb-1 text-sm underline"
                >
                  Trocar foto
                </button>
              </div>
            ) : (
              <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
                {fotos.map((foto) => {
                  const legenda = `${foto.consulta_data || "—"} · ${foto.origem_display || "Foto"}`;
                  return (
                    <button
                      key={foto.id}
                      type="button"
                      onClick={() => setFotoId(foto.id)}
                      className="overflow-hidden rounded-xl border-2 border-gray-200 text-left dark:border-gray-600"
                    >
                      <img src={foto.url} alt={legenda} className="aspect-square w-full object-cover" />
                      <span className="block bg-black/70 px-2 py-1 text-[10px] text-white">{legenda}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {MODOS.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setModo(item.id)}
                className="rounded-lg px-3 py-1.5 text-sm"
                style={{ backgroundColor: modo === item.id ? "var(--cb-primary, #8B3D52)" : "#f3f4f6", color: modo === item.id ? "#fff" : "#111" }}
              >
                {item.rotulo}
              </button>
            ))}
          </div>
          {modo !== "analise" && (
            <>
              <label className="block text-sm">
                Ajuste visual
                <select
                  className="mt-1 w-full rounded-lg border px-3 py-2 dark:border-gray-600 dark:bg-gray-900"
                  value={parametro}
                  onChange={(event) => setParametro(event.target.value)}
                >
                  {(OPCOES[modo] || []).map((opcao) => (
                    <option key={opcao.id} value={opcao.id}>{opcao.rotulo}</option>
                  ))}
                </select>
              </label>
              <label className="block text-sm">
                {textoIntensidade(modo, parametro, intensidade)}
                <input
                  type="range"
                  min={modo === "pele" ? 0.1 : -100}
                  max={modo === "pele" ? 1 : 100}
                  step={modo === "pele" ? 0.1 : 5}
                  value={intensidade}
                  onChange={(event) => setIntensidade(Number(event.target.value))}
                  className="mt-1 w-full"
                />
                <span className="mt-1 flex justify-between text-xs text-gray-500">
                  <span>{modo === "pele" ? "0,1 sutil" : (SENTIDO[parametro]?.negativo || "−100")}</span>
                  <span>{modo === "pele" ? "1,0 mais forte" : (SENTIDO[parametro]?.positivo || "100")}</span>
                </span>
              </label>
              <p className="text-xs text-gray-500">
                A YouCam recebe só {rotuloParametro(modo, parametro) || "este ajuste"}. Ela não aceita uma máscara desenhada; o efeito fica na região que o modelo reconhece para esse parâmetro.
              </p>
            </>
          )}
          {avisoProcedimento(selected.procedure_name || "", modo) && (
            <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              {avisoProcedimento(selected.procedure_name || "", modo)}
            </p>
          )}
          <label className="block text-sm">
            Quantidade planejada do produto
            <span className="mt-1 block text-xs text-gray-500">Este número não muda a imagem e não representa a dose do resultado.</span>
            <input
              type="number"
              min="0"
              step="0.1"
              value={quantidade}
              onChange={(event) => setQuantidade(event.target.value)}
              className="mt-1 w-full rounded-lg border px-3 py-2 dark:border-gray-600 dark:bg-gray-900"
            />
          </label>
          {erro && <p className="text-sm text-red-600">{erro}</p>}
          <button
            type="button"
            onClick={() => void gerar()}
            disabled={enviando}
            className="rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
            style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
          >
            {enviando ? "Enviando…" : "Gerar"}
          </button>
        </div>
      )}
      <div className="space-y-3">
        {resultados.filter((item) => item.status !== "erro").map((item) => {
          const par = Boolean(item.foto_url && item.resultado_url);
          const notas = item.leituras.filter((leitura) => leitura.nota != null && NOTAS[leitura.tipo]);
          const chaveOriginal = `${item.id}:original`;
          const chaveGerada = `${item.id}:gerada`;
          const duasMarcadas = Boolean(marcadas[chaveOriginal] && marcadas[chaveGerada]);
          const marcar = (chave: string) => setMarcadas((atual) => ({ ...atual, [chave]: !atual[chave] }));
          return (
          <article key={item.id} className="rounded-xl border border-gray-200 p-4 dark:border-gray-700">
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {MODOS.find((modoItem) => modoItem.id === item.modo)?.rotulo || item.modo}
                {item.parametro ? ` · ${rotuloParametro(item.modo, item.parametro) || item.parametro}` : ""}
                {item.intensidade != null ? ` · ${textoIntensidade(item.modo, item.parametro, item.intensidade)}` : ""}
                {item.status === "processando" ? " · processando" : ""}
              </p>
              <button
                type="button"
                onClick={() => void excluirGeracao(item.id)}
                disabled={excluindoId === item.id}
                className="inline-flex shrink-0 items-center gap-1 text-sm text-red-600 disabled:opacity-60"
              >
                <Trash2 size={14} />
                {excluindoId === item.id ? "Excluindo…" : "Excluir geração"}
              </button>
            </div>
            {par ? (
              <div className="mt-2 grid grid-cols-2 gap-3">
                {[
                  { chave: chaveOriginal, url: item.foto_url, legenda: "Original" },
                  { chave: chaveGerada, url: item.resultado_url, legenda: "Gerada" },
                ].map((lado) => (
                  <div
                    key={lado.chave}
                    className={`relative overflow-hidden rounded-xl border-2 ${
                      marcadas[lado.chave] ? "border-purple-600 ring-2 ring-purple-300" : "border-gray-200 dark:border-gray-600"
                    }`}
                  >
                    <img src={lado.url} alt={lado.legenda} className="aspect-[3/4] w-full object-cover" />
                    <button
                      type="button"
                      onClick={() => marcar(lado.chave)}
                      className={`absolute left-2 top-2 rounded-full p-1.5 text-white shadow ${
                        marcadas[lado.chave] ? "bg-purple-600" : "bg-black/50"
                      }`}
                      title={marcadas[lado.chave] ? "Desmarcar" : "Marcar para comparar"}
                    >
                      <Check size={14} />
                    </button>
                    <span className="absolute inset-x-0 bottom-0 bg-black/70 px-2 py-1 text-[10px] text-white">{lado.legenda}</span>
                  </div>
                ))}
              </div>
            ) : null}
            {par && <p className="mt-2 text-xs text-gray-600 dark:text-gray-300">{AVISO}</p>}
            {par && (
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className="text-xs text-gray-500">Marque as duas fotos para comparar</span>
                {duasMarcadas && (
                  <button
                    type="button"
                    onClick={() => setDual({ id: item.id, original: item.foto_url, gerada: item.resultado_url })}
                    className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-white"
                    style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
                  >
                    <Columns2 size={15} />
                    Comparar lado a lado
                  </button>
                )}
              </div>
            )}
            {notas.length > 0 && (
              <ul className="mt-2 text-sm text-gray-700 dark:text-gray-200">
                {notas.map((leitura) => (
                  <li key={`${item.id}-${leitura.tipo}`}>{NOTAS[leitura.tipo]}: {leitura.nota}</li>
                ))}
              </ul>
            )}
            {item.status === "pronta" && !item.ciencia_visual && (
              <button
                type="button"
                className="mt-2 text-sm underline"
                onClick={() => void ClinicaBelezaAPI.consultas.simulacao.ciencia(selected.id, item.id).then(() => {
                  setResultados((atual) => atual.map((linha) => linha.id === item.id ? { ...linha, ciencia_visual: true } : linha));
                })}
              >
                {par ? "Registrar que o paciente viu esta comparação" : "Registrar que o paciente viu estas notas"}
              </button>
            )}
            {item.ciencia_visual && (
              <p className="mt-2 text-xs text-gray-500">
                {par ? "O paciente viu esta comparação." : "O paciente viu estas notas."} Isso não é o termo do procedimento.
              </p>
            )}
            <dl className="mt-3 space-y-1 text-xs text-gray-600 dark:text-gray-300">
              <div>API: {item.api_nome || "Perfect Corp YouCam"} · {item.endpoint || ENDPOINTS[item.modo] || "—"}</div>
              <div>Data: {dataCurta(item.created_at) || "—"} · Profissional: {item.profissional_nome || selected.professional_name || "—"}</div>
              <div>Procedimento: {item.procedimento_nome || selected.procedure_name || "—"}</div>
              <div>Quantidade planejada: {item.quantidade != null ? item.quantidade : "não informada"}. Separada da intensidade visual.</div>
              {item.unidades != null && (
                <div>
                  Consumo: {item.unidades} {item.unidades === 1 ? "unidade" : "unidades"} YouCam desta clínica
                  {item.unidades_fonte === "tabela" ? ", pela tabela publicada. A resposta não traz o saldo." : "."}
                </div>
              )}
              {item.imagem_na_clinica && <div>A imagem gerada está no servidor de mídia da clínica.</div>}
            </dl>
          </article>
          );
        })}
      </div>
      {dual && (
        <ComparacaoDual
          original={dual.original}
          gerada={dual.gerada}
          excluindo={excluindoId === dual.id}
          onExcluir={() => void excluirGeracao(dual.id)}
          onClose={() => setDual(null)}
        />
      )}
    </div>
  );
}
