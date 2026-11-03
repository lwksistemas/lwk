"use client";

import { useEffect, useState } from "react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { formatCurrency } from "@/lib/financeiro-helpers";

interface CompraFornecedor {
  documento: string;
  fornecedor_nome: string;
  codigo: string;
  numero_nota: string;
  data_compra: string;
  quantidade: string;
  unidade: string;
  quantidade_estoque: string;
  unidade_estoque: string;
  fator: string;
  custo_unitario: string;
  lote: string;
  usuario: string;
}

interface LoteEstoque {
  codigo: string;
  validade: string;
  quantidade: string;
  fornecedor_nome: string;
  numero_nota: string;
  alerta_validade: boolean;
}

interface RespostaCompras {
  quantidade_atual: string;
  quantidade_em_lotes: string;
  quantidade_sem_lote: string;
  compras: CompraFornecedor[];
  lotes: LoteEstoque[];
}

function dataCurta(valor: string): string {
  const dia = (valor || "").slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dia)) return "—";
  const [ano, mes, d] = dia.split("-");
  return `${d}/${mes}/${ano}`;
}

function documentoCurto(doc: string): string {
  const digitos = (doc || "").replace(/\D/g, "");
  return digitos || "—";
}

export function EstoqueProdutoCompras({ produtoId }: { produtoId: number }) {
  const [dados, setDados] = useState<RespostaCompras | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    let ativo = true;
    void clinicaBelezaFetch(`/estoque/${produtoId}/compras/`)
      .then(async (res) => {
        const corpo = await res.json().catch(() => null);
        if (!res.ok) throw new Error("Não foi possível carregar o histórico.");
        if (ativo) setDados(corpo as RespostaCompras);
      })
      .catch(() => {
        if (ativo) setErro("Não foi possível carregar fornecedores e lotes.");
      });
    return () => {
      ativo = false;
    };
  }, [produtoId]);

  return (
    <div className="px-5 py-4 border-t border-gray-200 dark:border-neutral-700 space-y-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
        Fornecedores e histórico de compras
      </p>
      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {!dados && !erro && <p className="text-sm text-gray-500">Carregando…</p>}
      {dados && dados.compras.length === 0 && (
        <p className="text-sm text-gray-500">Nenhuma compra por NF-e neste produto ainda.</p>
      )}
      {dados && dados.compras.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="text-gray-500">
              <tr>
                <th className="py-1 pr-2 font-medium">Fornecedor</th>
                <th className="py-1 pr-2 font-medium">NF</th>
                <th className="py-1 pr-2 font-medium">Data</th>
                <th className="py-1 pr-2 font-medium">Qtd</th>
                <th className="py-1 pr-2 font-medium">Fator</th>
                <th className="py-1 pr-2 font-medium">Custo</th>
                <th className="py-1 font-medium">Lote</th>
              </tr>
            </thead>
            <tbody>
              {dados.compras.map((compra, i) => {
                const anterior = dados.compras.slice(i + 1).find((item) => item.documento === compra.documento);
                const mudou = anterior && anterior.custo_unitario !== compra.custo_unitario;
                return (
                  <tr key={`${compra.numero_nota}-${i}`} className="border-t border-gray-100 dark:border-neutral-700">
                    <td className="py-1.5 pr-2">
                      <span className="block text-gray-900 dark:text-gray-100">{compra.fornecedor_nome || "Fornecedor"}</span>
                      <span className="text-gray-500">{documentoCurto(compra.documento)}{compra.codigo ? ` · ${compra.codigo}` : ""}</span>
                    </td>
                    <td className="py-1.5 pr-2">{compra.numero_nota || "—"}</td>
                    <td className="py-1.5 pr-2">{dataCurta(compra.data_compra)}</td>
                    <td className="py-1.5 pr-2">{compra.quantidade_estoque} {compra.unidade_estoque}</td>
                    <td className="py-1.5 pr-2">{Number(compra.fator).toString()}</td>
                    <td className="py-1.5 pr-2">
                      {formatCurrency(compra.custo_unitario)}
                      {mudou ? " · preço diferente" : ""}
                    </td>
                    <td className="py-1.5">{compra.lote || "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {dados && dados.lotes.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">
            Lotes com saldo: {dados.quantidade_em_lotes}
            {Number(dados.quantidade_sem_lote) > 0 ? ` · ${dados.quantidade_sem_lote} sem lote rastreado` : ""}
          </p>
          <ul className="space-y-1">
            {dados.lotes.map((lote) => (
              <li key={`${lote.codigo}-${lote.validade}`} className="text-xs text-gray-700 dark:text-gray-200">
                {lote.codigo || "Sem número"} · {lote.quantidade}
                {lote.validade ? ` · val ${dataCurta(lote.validade)}` : ""}
                {lote.numero_nota ? ` · NF ${lote.numero_nota}` : ""}
                {lote.alerta_validade ? " · validade próxima" : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
