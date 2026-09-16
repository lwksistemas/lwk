"use client";

import { Ban, Check, Eye, FileText, Mail, MessageCircle, Plus, Trash2 } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { formatarObservacoesOrcamento, STATUS_LABEL, statusBadgeClass } from "./orcamento-tab-utils";
import type { Orcamento } from "./types";

interface OrcamentoCardProps {
  orc: Orcamento;
  abrindoPdf: number | null;
  decidindoStatus: number | null;
  onVisualizar: (orc: Orcamento) => void;
  onPdf: (id: number) => void;
  onEnviar: (id: number, canal: "email" | "whatsapp") => void;
  onAceitar: (id: number) => void;
  onRecusar: (id: number) => void;
  onEditar: (orc: Orcamento) => void;
  onExcluir: (id: number) => void;
}

export function OrcamentoCard({
  orc,
  abrindoPdf,
  decidindoStatus,
  onVisualizar,
  onPdf,
  onEnviar,
  onAceitar,
  onRecusar,
  onEditar,
  onExcluir,
}: OrcamentoCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-lg font-semibold text-gray-900 dark:text-white">
            {formatCurrency(orc.valor_total)}
          </span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${statusBadgeClass(orc.status)}`}>
            {STATUS_LABEL[orc.status] || orc.status}
          </span>
          {orc.enviado_email && <span className="text-xs text-green-600">✓ E-mail</span>}
          {orc.enviado_whatsapp && <span className="text-xs text-green-600">✓ WhatsApp</span>}
        </div>
        <span className="text-xs text-gray-500">
          {new Date(orc.created_at).toLocaleDateString("pt-BR")}
        </span>
      </div>

      <div className="text-sm text-gray-800 dark:text-gray-200 mb-3 space-y-1">
        {orc.itens.map((it) => (
          <div key={it.id} className="flex justify-between gap-3">
            <span className="break-words">
              {it.nome_procedimento}{" "}
              <span className="text-gray-500">({it.quantidade}x)</span>
            </span>
            <span className="shrink-0 font-medium">{formatCurrency(it.subtotal)}</span>
          </div>
        ))}
      </div>

      {orc.observacoes && (
        <div className="mb-3 rounded-md bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-700 px-3 py-2 max-h-48 overflow-y-auto">
          <p className="text-xs font-medium text-gray-500 mb-1">Observações</p>
          <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap break-words leading-relaxed">
            {formatarObservacoesOrcamento(orc.observacoes)}
          </p>
        </div>
      )}

      <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100 dark:border-gray-700">
        <button
          type="button"
          onClick={() => onVisualizar(orc)}
          className="flex items-center gap-1 px-3 py-1.5 text-xs bg-gray-100 text-gray-800 rounded hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
        >
          <Eye size={14} /> Visualizar
        </button>
        <button
          type="button"
          onClick={() => onPdf(orc.id)}
          disabled={abrindoPdf === orc.id}
          className="flex items-center gap-1 px-3 py-1.5 text-xs bg-purple-50 text-purple-700 rounded hover:bg-purple-100 dark:bg-purple-900/20 dark:text-purple-300 disabled:opacity-50"
        >
          <FileText size={14} /> {abrindoPdf === orc.id ? "Abrindo..." : "PDF"}
        </button>
        <button
          type="button"
          onClick={() => onEnviar(orc.id, "email")}
          className="flex items-center gap-1 px-3 py-1.5 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 dark:bg-blue-900/20 dark:text-blue-300"
        >
          <Mail size={14} /> Email
        </button>
        <button
          type="button"
          onClick={() => onEnviar(orc.id, "whatsapp")}
          className="flex items-center gap-1 px-3 py-1.5 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100 dark:bg-green-900/20 dark:text-green-300"
        >
          <MessageCircle size={14} /> WhatsApp
        </button>
        {orc.status !== "ACEITO" && (
          <button
            type="button"
            onClick={() => onAceitar(orc.id)}
            disabled={decidindoStatus === orc.id}
            className="flex items-center gap-1 px-3 py-1.5 text-xs bg-emerald-50 text-emerald-800 rounded hover:bg-emerald-100 dark:bg-emerald-900/20 dark:text-emerald-300 disabled:opacity-50"
          >
            <Check size={14} /> Aceitar
          </button>
        )}
        {orc.status !== "RECUSADO" && (
          <button
            type="button"
            onClick={() => onRecusar(orc.id)}
            disabled={decidindoStatus === orc.id}
            className="flex items-center gap-1 px-3 py-1.5 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100 dark:bg-red-900/20 dark:text-red-300 disabled:opacity-50"
          >
            <Ban size={14} /> Recusar
          </button>
        )}
        {orc.status !== "ACEITO" && (
          <button
            type="button"
            onClick={() => onEditar(orc)}
            className="flex items-center gap-1 px-3 py-1.5 text-xs bg-amber-50 text-amber-700 rounded hover:bg-amber-100 dark:bg-amber-900/20 dark:text-amber-300"
          >
            <Plus size={14} /> Editar
          </button>
        )}
        {orc.status !== "ACEITO" && (
          <button
            type="button"
            onClick={() => onExcluir(orc.id)}
            className="flex items-center gap-1 px-3 py-1.5 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100 dark:bg-red-900/20 dark:text-red-300 ml-auto"
          >
            <Trash2 size={14} /> Excluir
          </button>
        )}
      </div>
    </div>
  );
}
