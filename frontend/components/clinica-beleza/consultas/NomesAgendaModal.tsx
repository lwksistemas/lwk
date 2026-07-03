"use client";

import { CalendarDays, Loader2, Plus } from "lucide-react";
import { ClinicaBelezaPortraitModal } from "@/components/clinica-beleza/ClinicaBelezaPortraitModal";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { NomeAgendaFormSection } from "./nomes-agenda/NomeAgendaFormSection";
import { NomeAgendaListItem } from "./nomes-agenda/NomeAgendaListItem";
import { useNomesAgenda } from "./nomes-agenda/useNomesAgenda";

interface NomesAgendaModalProps {
  open: boolean;
  onClose: () => void;
}

export function NomesAgendaModal({ open, onClose }: NomesAgendaModalProps) {
  const {
    nomes,
    loading,
    saving,
    editingId,
    isCreating,
    formNome,
    error,
    formBusy,
    showForm,
    setFormNome,
    resetForm,
    startNew,
    startEdit,
    handleSave,
    handleSetPadrao,
    handleDelete,
  } = useNomesAgenda(open);

  return (
    <ClinicaBelezaPortraitModal
      open={open}
      onClose={onClose}
      title="Nomes de Agenda"
      subtitle="Cadastre os nomes usados ao agendar (ex: Estética, Dermatologia)"
      icon={<CalendarDays size={20} className="text-purple-600 shrink-0 mt-0.5" />}
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
              Novo nome
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

      {showForm && (
        <NomeAgendaFormSection
          formNome={formNome}
          editingId={editingId}
          saving={saving}
          onNomeChange={setFormNome}
          onSave={() => void handleSave()}
          onCancel={resetForm}
        />
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500">
          <Loader2 size={24} className="animate-spin mx-auto mb-2" />
          Carregando...
        </div>
      ) : nomes.length === 0 && !isCreating ? (
        <p className="text-center text-gray-500 text-sm py-8">Nenhum nome cadastrado.</p>
      ) : (
        <ul className="space-y-2">
          {nomes.map((item) => (
            <NomeAgendaListItem
              key={item.id}
              item={item}
              isEditing={editingId === item.id}
              formBusy={formBusy}
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
