"use client";

import { useEffect, useState } from "react";
import { AlertCircle } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import type { CandidatoProdutoXml, PreviewResult, ProdutoPreview } from "./estoque-importar-xml-types";
import { custoUnitarioConvertido, formatProdutoPreviewLine, itemPrecisaConfirmacao, opcoesEntradaEstoque, quantidadeEntrada, resumoConferencia, textoItensPendentes, textoPagamentoNota, textoResumoConferencia } from "./estoque-importar-xml-utils";
import type { EstoqueCategoria } from "./estoque-types";
import { ESTOQUE_CATEGORIAS } from "./estoque-types";

function formatValorNota(valor: string | number | null | undefined): string {
  if (valor == null || valor === "") return "";
  const n = typeof valor === "number" ? valor : Number(String(valor).replace(",", "."));
  if (!Number.isFinite(n)) return "";
  return formatCurrency(n);
}

interface EstoqueImportarXmlPreviewProps {
  preview: PreviewResult;
  categorias?: EstoqueCategoria[];
  onProdutoCategoriaChange?: (index: number, slug: string, categoriaId?: number | null) => void;
  onProdutoChange?: (index: number, patch: Partial<ProdutoPreview>) => void;
  onAplicarIguais?: (index: number) => void;
}

const COLUNAS = "sm:grid sm:grid-cols-[minmax(0,1.5fr)_minmax(0,0.7fr)_8rem_11rem] sm:gap-3 sm:items-center";

export function EstoqueImportarXmlPreview({
  preview,
  categorias,
  onProdutoCategoriaChange,
  onProdutoChange,
  onAplicarIguais,
}: EstoqueImportarXmlPreviewProps) {
  const options =
    categorias && categorias.length > 0
      ? categorias.map((c) => ({ value: c.slug, id: c.id, label: c.nome }))
      : ESTOQUE_CATEGORIAS.map((c) => ({ value: c.value, id: null as number | null, label: c.label }));

  const handleChange = (index: number, slug: string) => {
    const opt = options.find((o) => o.value === slug);
    onProdutoCategoriaChange?.(index, slug, opt?.id ?? null);
  };

  const resumo = resumoConferencia(preview.produtos);
  const [destaque, setDestaque] = useState<number | null>(null);
  const avisoPendentes = textoItensPendentes(resumo.pendentesNumeros);

  const irParaItem = (numero: number) => {
    setDestaque(numero);
    document.getElementById(`nfe-item-${numero}`)?.scrollIntoView({ block: "center", behavior: "smooth" });
  };

  return (
    <div>
      {preview.aviso_destinatario && (
        <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 mb-3 flex items-start gap-2">
          <AlertCircle size={16} className="shrink-0 mt-0.5 text-amber-600" />
          <p className="text-sm text-amber-800 dark:text-amber-200">
            <strong>Atenção:</strong> {preview.aviso_destinatario}
          </p>
        </div>
      )}
      <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 mb-3">
        <p className="text-sm font-medium text-blue-800 dark:text-blue-200 flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <span>
            NF nº {preview.nota.numero || "—"} — {preview.nota.fornecedor || "Fornecedor"}
          </span>
          {formatValorNota(preview.nota.valor_total) ? (
            <span className="font-semibold whitespace-nowrap">
              · Total {formatValorNota(preview.nota.valor_total)}
            </span>
          ) : null}
        </p>
        <p className="text-xs text-blue-600 dark:text-blue-400">
          {textoResumoConferencia(resumo)}
        </p>
        {textoPagamentoNota(preview.pagamento) ? (
          <p className="text-xs text-blue-800 dark:text-blue-200 mt-1">{textoPagamentoNota(preview.pagamento)}</p>
        ) : null}
        {avisoPendentes ? (
          <p className="text-xs text-amber-800 dark:text-amber-200 mt-1">
            {resumo.pendentesNumeros.length === 1 ? "Falta confirmar o item " : "Falta confirmar os itens "}
            {resumo.pendentesNumeros.map((numero, indice) => {
              const ultimo = indice === resumo.pendentesNumeros.length - 1;
              const penultimo = indice === resumo.pendentesNumeros.length - 2;
              return (
                <span key={numero}>
                  <button
                    type="button"
                    onClick={() => irParaItem(numero)}
                    className="font-semibold underline"
                  >
                    {numero}
                  </button>
                  {ultimo ? "." : penultimo && resumo.pendentesNumeros.length > 1 ? " e " : ", "}
                </span>
              );
            })}
          </p>
        ) : null}
      </div>

      <div className="border border-gray-200 dark:border-neutral-700 rounded-lg overflow-hidden">
        <div className={`hidden ${COLUNAS} px-3 py-2 text-[11px] uppercase tracking-wide text-gray-500 bg-gray-50 dark:bg-neutral-800/80 border-b border-gray-200 dark:border-neutral-700`}>
          <span>Produto</span>
          <span>Quantidade / valor</span>
          <span>Categoria</span>
          <span>Entrada</span>
        </div>
        <div className="max-h-[min(32rem,60vh)] overflow-y-auto divide-y divide-gray-100 dark:divide-neutral-700">
          {preview.produtos.map((p: ProdutoPreview, i) => {
            const numero = i + 1;
            const pendente = itemPrecisaConfirmacao(p);
            return (
            <div
              key={i}
              id={`nfe-item-${numero}`}
              className={`px-3 py-2 text-sm space-y-1.5 ${pendente ? "bg-amber-50 dark:bg-amber-950/30" : ""} ${destaque === numero ? "ring-2 ring-inset ring-amber-400" : ""}`}
            >
              <div className={COLUNAS}>
                <div className="min-w-0">
                  <p className="font-medium text-gray-900 dark:text-gray-100 break-words leading-snug">
                    <span className="text-gray-500 dark:text-gray-400 tabular-nums mr-1">{numero}.</span>
                    {p.nome}
                  </p>
                  {p.alerta && (
                    <p className="text-[11px] text-amber-700 dark:text-amber-300 mt-0.5">{p.alerta}</p>
                  )}
                  {p.acao === "novo" && (
                    <label className="block mt-1">
                      <span className="text-[11px] text-gray-500 dark:text-gray-400">Nome comercial</span>
                      <input
                        value={p.nome_comercial ?? p.nome}
                        maxLength={200}
                        placeholder="No recibo e na consulta"
                        onChange={(e) => onProdutoChange?.(i, { nome_comercial: e.target.value })}
                        className="mt-0.5 w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800"
                      />
                    </label>
                  )}
                  <p className="sm:hidden text-xs text-gray-500 dark:text-gray-400">
                    {formatProdutoPreviewLine(p)}
                  </p>
                </div>
                <p className="hidden sm:block text-xs text-gray-600 dark:text-gray-300">
                  {p.quantidade} {p.unidade_medida} × R$ {Number(p.preco_custo || 0).toFixed(2)}
                </p>
                {onProdutoCategoriaChange ? (
                  <select
                    value={p.categoria || "outro"}
                    onChange={(e) => handleChange(i, e.target.value)}
                    className="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800"
                  >
                    {options.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span className="text-xs text-gray-500">{p.categoria || "—"}</span>
                )}
                <AcaoItem produto={p} onChange={(patch) => onProdutoChange?.(i, patch)} />
              </div>
              <LinhaFatorLote produto={p} onChange={(patch) => onProdutoChange?.(i, patch)} />
              {p.grupo && preview.produtos.filter((outro) => outro.grupo === p.grupo).length > 1 && (
                <button
                  type="button"
                  disabled={!p.acao || (p.acao === "vincular" && !p.produto_id)}
                  onClick={() => onAplicarIguais?.(i)}
                  className="text-[11px] text-blue-700 dark:text-blue-300 disabled:opacity-40 hover:underline"
                >
                  Aplicar a mesma decisão aos itens idênticos
                </button>
              )}
            </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function AcaoItem({
  produto,
  onChange,
}: {
  produto: ProdutoPreview;
  onChange: (patch: Partial<ProdutoPreview>) => void;
}) {
  const opcoes = opcoesDoProduto(produto);
  return (
    <div className="space-y-1">
      <select
        value={produto.acao || ""}
          onChange={(e) => {
          const acao = e.target.value as ProdutoPreview["acao"];
          const patch: Partial<ProdutoPreview> = { acao };
          if (acao !== "vincular") patch.exige_lote = false;
          if (acao === "vincular" && !produto.produto_id && opcoes[0]) {
            patch.produto_id = opcoes[0].id;
            patch.produto_nome = opcoes[0].nome;
            patch.exige_lote = !!opcoes[0].exige_lote;
          }
          onChange(patch);
        }}
        className="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800"
      >
        <option value="">Confirme</option>
        <option value="vincular">Vincular</option>
        <option value="novo">Cadastrar novo</option>
        <option value="ignorar">Ignorar</option>
      </select>
      {produto.acao === "vincular" && (
        <>
          <select
            value={produto.produto_id ?? ""}
            onChange={(e) => {
              const id = Number(e.target.value);
              const escolhido = opcoes.find((c) => c.id === id);
              onChange({
                produto_id: id || null,
                produto_nome: escolhido?.nome || produto.produto_nome,
                exige_lote: !!escolhido?.exige_lote,
              });
            }}
            className="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800"
          >
            <option value="">Escolha o produto</option>
            {opcoes.map((c) => (
              <option key={c.id} value={c.id}>{c.nome}</option>
            ))}
          </select>
          <BuscaProduto
            onEscolher={(id, nome, exigeLote) => onChange({
              produto_id: id,
              produto_nome: nome,
              exige_lote: exigeLote,
              candidatos: [{ id, nome, exige_lote: exigeLote }, ...(produto.candidatos || []).filter((c) => c.id !== id)].slice(0, 8),
            })}
          />
        </>
      )}
    </div>
  );
}

function LinhaFatorLote({
  produto,
  onChange,
}: {
  produto: ProdutoPreview;
  onChange: (patch: Partial<ProdutoPreview>) => void;
}) {
  const opcoes = opcoesEntradaEstoque(produto);
  const fatorAtual = Number(produto.fator || "1");
  const mostraConversao = Number.isFinite(fatorAtual) && fatorAtual !== 1;
  const escolher = (fator: string, unidade: string) => onChange({ fator, unidade_estoque: unidade });
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-gray-500">
      {opcoes && (
        <div className="flex flex-wrap items-center gap-1">
          <span>Entrada no estoque</span>
          {opcoes.map((opcao) => {
            const selecionada = Number(opcao.fator) === fatorAtual;
            return (
              <button
                key={opcao.id}
                type="button"
                onClick={() => escolher(opcao.fator, opcao.unidade)}
                className={`px-2 py-1 rounded border ${selecionada ? "border-[#8B3D52] bg-[#8B3D52]/10 text-gray-900 dark:text-gray-100" : "border-gray-300 dark:border-neutral-600 text-gray-600 dark:text-gray-300"}`}
              >
                {opcao.rotulo}
              </button>
            );
          })}
        </div>
      )}
      <label className="flex items-center gap-1">
        {opcoes ? "Por item da nota" : "Fator"}
        <input
          type="number"
          min="0.01"
          step="1"
          value={produto.fator || "1"}
          onChange={(e) => escolher(e.target.value, Number(e.target.value) === 1 ? (produto.unidade_medida || "un") : (opcoes?.find((o) => o.id === "conteudo")?.unidade || produto.unidade_estoque || produto.unidade_medida || "un"))}
          className="w-14 px-1.5 py-1 border border-gray-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800 text-gray-800 dark:text-gray-100"
        />
      </label>
      {mostraConversao && (
        <span className="text-gray-800 dark:text-gray-100">
          {quantidadeEntrada(produto)} {produto.unidade_estoque || produto.unidade_medida} a R$ {custoUnitarioConvertido(produto)}
          {(Number(produto.valor_desconto || "0") > 0 || Number(produto.valor_despesas || "0") > 0) ? " líquido" : ""}
        </span>
      )}
      {produto.exige_lote && (!(produto.lote || "").trim() || !(produto.validade || "").trim()) && (
        <span className="text-amber-700 dark:text-amber-300">exige lote e validade</span>
      )}
      <label className="flex items-center gap-1">
        Lote
        <input
          value={produto.lote || ""}
          onChange={(e) => onChange({ lote: e.target.value })}
          placeholder="Lote"
          className="w-28 px-1.5 py-1 border border-gray-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800 text-gray-800 dark:text-gray-100"
        />
      </label>
      <input
        type="date"
        aria-label="Validade"
        value={(produto.validade || "").slice(0, 10)}
        onChange={(e) => onChange({ validade: e.target.value || null })}
        className="px-1.5 py-1 border border-gray-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800 text-gray-800 dark:text-gray-100"
      />
    </div>
  );
}

function opcoesDoProduto(produto: ProdutoPreview): CandidatoProdutoXml[] {
  const opcoes = [...(produto.candidatos || [])];
  if (produto.produto_id && !opcoes.some((c) => c.id === produto.produto_id)) {
    opcoes.unshift({ id: produto.produto_id, nome: produto.produto_nome || `Produto ${produto.produto_id}` });
  }
  return opcoes;
}

function BuscaProduto({ onEscolher }: { onEscolher: (id: number, nome: string, exigeLote: boolean) => void }) {
  const [q, setQ] = useState("");
  const [itens, setItens] = useState<CandidatoProdutoXml[]>([]);

  useEffect(() => {
    const termo = q.trim();
    if (termo.length < 2) {
      setItens([]);
      return;
    }
    const timer = setTimeout(() => {
      void clinicaBelezaFetch(`/estoque/?search=${encodeURIComponent(termo)}`)
        .then((res) => res.json())
        .then((data) => {
          const rows = Array.isArray(data) ? data : data?.results || [];
          setItens(rows.slice(0, 8).map((r: { id: number; nome: string; exige_lote?: boolean }) => ({
            id: r.id,
            nome: r.nome,
            exige_lote: !!r.exige_lote,
          })));
        })
        .catch(() => setItens([]));
    }, 300);
    return () => clearTimeout(timer);
  }, [q]);

  return (
    <div>
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Buscar outro produto"
        className="w-full px-2 py-1 text-[11px] border border-gray-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800"
      />
      {itens.length > 0 && (
        <ul className="mt-1 max-h-24 overflow-y-auto border border-gray-200 dark:border-neutral-700 rounded">
          {itens.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className="w-full text-left px-2 py-1 text-[11px] hover:bg-gray-50 dark:hover:bg-neutral-800"
                onClick={() => {
                  onEscolher(item.id, item.nome, !!item.exige_lote);
                  setQ("");
                  setItens([]);
                }}
              >
                {item.nome}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
