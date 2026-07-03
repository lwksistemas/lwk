"use client";

import { Loader2, Plus } from "lucide-react";
import { ClinicaBelezaPortraitModal } from "@/components/clinica-beleza/ClinicaBelezaPortraitModal";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { LocalAtendimentoFormFields } from "./locais-atendimento/LocalAtendimentoFormFields";
import { LocalAtendimentoListItem } from "./locais-atendimento/LocalAtendimentoListItem";
import { useLocaisAtendimento } from "./locais-atendimento/useLocaisAtendimento";

interface LocaisAtendimentoModalProps {
  open: boolean;
  onClose: () => void;
}

export function LocaisAtendimentoModal({ open, onClose }: LocaisAtendimentoModalProps) {
  const {
    locais,
    loading,
    saving,
    editingId,
    isCreating,
    formNome,
    formValor,
    error,
    formBusy,
    setFormNome,
    setFormValor,
    resetForm,
    startEdit,
    startNew,
    handleSave,
    handleSetPadrao,
    handleDelete,
  } = useLocaisAtendimento(open);

  return (
    <ClinicaBelezaPortraitModal
      open={open}
      onClose={onClose}
      title="Locais de Atendimento"
      subtitle="Cadastre consultório, home care e outros locais"
      footer={
        <div className="flex justify-between gap-2">
          {!formBusy && (
            <button
              type="button"
              onClick={startNew}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-white"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Plus size={14} />
              Novo local
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 ml-auto"
          >
            Fechar
          </button>
        </div>
      }
    >
      {error && (
        <div className="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {isCreating && (
        <div className="mb-4 p-3 rounded-lg border-2 border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-900/10">
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Novo local</p>
          <LocalAtendimentoFormFields
            formNome={formNome}
            formValor={formValor}
            onNomeChange={setFormNome}
            onValorChange={setFormValor}
            onSave={() => void handleSave()}
            onCancel={resetForm}
            saving={saving}
            saveLabel="Adicionar"
          />
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500">
          <Loader2 size={24} className="animate-spin mx-auto mb-2" />
          Carregando...
        </div>
      ) : locais.length === 0 && !isCreating ? (
        <p className="text-center text-gray-500 dark:text-gray-400 text-sm py-8">
          Nenhum local cadastrado.
        </p>
      ) : (
        <ul className="space-y-2">
          {locais.map((local) => (
            <LocalAtendimentoListItem
              key={local.id}
              local={local}
              isEditing={editingId === local.id}
              formBusy={formBusy}
              formNome={formNome}
              formValor={formValor}
              saving={saving}
              onNomeChange={setFormNome}
              onValorChange={setFormValor}
              onSave={() => void handleSave()}
              onCancel={resetForm}
              onSetPadrao={(id) => void handleSetPadrao(id)}
              onStartEdit={startEdit}
              onDelete={(id) => void handleDelete(id)}
            />
          ))}
        </ul>
      )}
    </ClinicaBelezaPortraitModal>
  );
}
