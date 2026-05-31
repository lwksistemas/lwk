import { Pencil, Save, X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import type { Protocolo } from "./consultas-types";
import { PreviewBlock } from "./PreviewBlock";

export function ConsultaAtendimentoTab({
  protocolos,
  protocoloPreview,
  editAtendimento,
  observacoes,
  observacoesDraft,
  saving,
  onSelectProtocolo,
  onConfirmProtocolo,
  onCancelProtocolo,
  onStartEdit,
  onCancelEdit,
  onChangeDraft,
  onSave,
}: {
  protocolos: Protocolo[];
  protocoloPreview: Protocolo | null;
  editAtendimento: boolean;
  observacoes: string;
  observacoesDraft: string;
  saving: boolean;
  onSelectProtocolo: (id: number) => void;
  onConfirmProtocolo: () => void;
  onCancelProtocolo: () => void;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onChangeDraft: (v: string) => void;
  onSave: () => void;
}) {
  return (
    <div className="space-y-5">
      {protocolos.length > 0 && !editAtendimento && (
        <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4">
          <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">Protocolo cadastrado</p>
          {!protocoloPreview ? (
            <select
              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600 text-sm"
              value=""
              onChange={(e) => {
                const pid = Number(e.target.value);
                if (pid) onSelectProtocolo(pid);
              }}
              disabled={saving}
            >
              <option value="">Selecionar para ver preview...</option>
              {protocolos.map((p) => (
                <option key={p.id} value={p.id}>{p.nome}</option>
              ))}
            </select>
          ) : (
            <div className="space-y-3">
              <p className="font-semibold text-gray-900 dark:text-gray-100">{protocoloPreview.nome}</p>
              {protocoloPreview.preparacao && <PreviewBlock label="Preparação" value={protocoloPreview.preparacao} />}
              {protocoloPreview.execucao && <PreviewBlock label="Execução" value={protocoloPreview.execucao} mono />}
              {protocoloPreview.pos_procedimento && <PreviewBlock label="Pós-procedimento" value={protocoloPreview.pos_procedimento} />}
              {protocoloPreview.materiais_necessarios && <PreviewBlock label="Materiais" value={protocoloPreview.materiais_necessarios} />}
              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={onConfirmProtocolo}
                  disabled={saving}
                  className="px-4 py-2 rounded-lg text-white text-sm disabled:opacity-50"
                  style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                >
                  Aplicar protocolo
                </button>
                <button
                  type="button"
                  onClick={onCancelProtocolo}
                  className="px-4 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">Notas do atendimento</h3>
          {!editAtendimento ? (
            <button
              type="button"
              onClick={onStartEdit}
              className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700"
            >
              <Pencil size={14} />
              Editar
            </button>
          ) : (
            <button type="button" onClick={onCancelEdit} className="inline-flex items-center gap-1.5 text-sm text-gray-500">
              <X size={14} />
              Cancelar
            </button>
          )}
        </div>
        {!editAtendimento ? (
          <PreviewBlock label="Conteúdo" value={observacoes} empty="Nenhuma anotação registrada." mono />
        ) : (
          <>
            <textarea
              rows={12}
              value={observacoesDraft}
              onChange={(e) => onChangeDraft(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600 font-mono text-sm"
            />
            <button
              type="button"
              onClick={onSave}
              disabled={saving}
              className="mt-3 flex items-center gap-2 px-4 py-2 rounded-lg text-white disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Save size={18} />
              {saving ? "Salvando..." : "Salvar atendimento"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
