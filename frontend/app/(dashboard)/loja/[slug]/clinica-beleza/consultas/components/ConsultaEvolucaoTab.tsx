import { Pencil, X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import type { Evolucao } from "./consultas-types";
import { PreviewBlock } from "./PreviewBlock";

interface EvolucaoForm {
  descricao: string;
  procedimento_realizado: string;
  produtos_utilizados: string;
  orientacoes: string;
  satisfacao: string;
}

export function ConsultaEvolucaoTab({
  evolucoes,
  editEvolucao,
  evolucaoForm,
  saving,
  formatData,
  onStartEdit,
  onCancelEdit,
  onChangeForm,
  onSave,
}: {
  evolucoes: Evolucao[];
  editEvolucao: boolean;
  evolucaoForm: EvolucaoForm;
  saving: boolean;
  formatData: (d?: string | null) => string;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onChangeForm: React.Dispatch<React.SetStateAction<EvolucaoForm>>;
  onSave: () => void;
}) {
  return (
    <div className="space-y-5">
      {evolucoes.length > 0 && (
        <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6 space-y-4">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">Registros desta consulta</h3>
          {evolucoes.map((ev) => (
            <div key={ev.id} className="rounded-lg border border-gray-100 dark:border-neutral-700 p-4 space-y-2">
              <p className="text-xs text-gray-500">
                {formatData(ev.created_at)}
                {ev.professional_name ? ` · ${ev.professional_name}` : ""}
              </p>
              {ev.descricao && <PreviewBlock label="Evolução" value={ev.descricao} />}
              {ev.procedimento_realizado && <PreviewBlock label="Procedimento" value={ev.procedimento_realizado} />}
              {ev.produtos_utilizados && <PreviewBlock label="Produtos" value={ev.produtos_utilizados} />}
              {ev.orientacoes && <PreviewBlock label="Orientações" value={ev.orientacoes} />}
            </div>
          ))}
        </div>
      )}

      <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">Nova evolução</h3>
          {!editEvolucao ? (
            <button
              type="button"
              onClick={onStartEdit}
              className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg text-white"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Pencil size={14} />
              Registrar
            </button>
          ) : (
            <button type="button" onClick={onCancelEdit} className="inline-flex items-center gap-1.5 text-sm text-gray-500">
              <X size={14} />
              Cancelar
            </button>
          )}
        </div>
        {!editEvolucao ? (
          <p className="text-sm text-gray-500">Clique em Registrar para adicionar uma evolução nesta consulta.</p>
        ) : (
          <div className="space-y-3">
            <textarea placeholder="Evolução / observações clínicas" rows={3} value={evolucaoForm.descricao} onChange={(e) => onChangeForm((f) => ({ ...f, descricao: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600" />
            <textarea placeholder="Procedimento realizado" rows={2} value={evolucaoForm.procedimento_realizado} onChange={(e) => onChangeForm((f) => ({ ...f, procedimento_realizado: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600" />
            <textarea placeholder="Produtos utilizados" rows={2} value={evolucaoForm.produtos_utilizados} onChange={(e) => onChangeForm((f) => ({ ...f, produtos_utilizados: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600" />
            <textarea placeholder="Orientações ao cliente" rows={2} value={evolucaoForm.orientacoes} onChange={(e) => onChangeForm((f) => ({ ...f, orientacoes: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600" />
            <select value={evolucaoForm.satisfacao} onChange={(e) => onChangeForm((f) => ({ ...f, satisfacao: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600">
              <option value="">Satisfação (opcional)</option>
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
            <button type="button" onClick={onSave} disabled={saving} className="px-4 py-2 rounded-lg text-white disabled:opacity-50" style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}>
              Confirmar evolução
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
