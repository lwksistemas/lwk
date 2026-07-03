"use client";

/**
 * Página dedicada para cadastro/edição de profissional — Clínica da Beleza.
 * Seções: Dados Básicos, Prescritor (Memed), Comissões, Acesso.
 */

import { Save } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ProfissionalAcessoSection } from "./ProfissionalAcessoSection";
import { ProfissionalComissaoConsultaBlock } from "./ProfissionalComissaoConsultaBlock";
import { ProfissionalComissaoProcedimentoBlock } from "./ProfissionalComissaoProcedimentoBlock";
import { ProfissionalDadosBasicosSection } from "./ProfissionalDadosBasicosSection";
import { ProfissionalPrescritorSection } from "./ProfissionalPrescritorSection";
import { useProfissionalForm } from "./useProfissionalForm";

interface ProfissionalFormPageContentProps {
  slug: string;
  editId: string | null;
  onDone: () => void;
}

export function ProfissionalFormPageContent({ slug, editId, onDone }: ProfissionalFormPageContentProps) {
  const {
    form,
    setField,
    locais,
    convenios,
    procedures,
    error,
    loading,
    saving,
    salvar,
    comissoes,
    comissoesConsultaLocal,
    addComissao,
    addComissaoConsultaLocal,
    removeComissaoConsultaLocal,
    updateComissaoConsultaLocal,
    removeComissao,
    updateComissao,
    locaisDisponiveisConsulta,
  } = useProfissionalForm(editId, onDone);

  if (loading) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader title="Profissional" />
        <ClinicaBelezaPageContent>
          <div className="text-center py-16 text-gray-500">Carregando...</div>
        </ClinicaBelezaPageContent>
      </>
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={editId ? "Editar Profissional" : "Novo Profissional"}
        backHref={`/loja/${slug}/clinica-beleza/profissionais`}
      />
      <ClinicaBelezaPageContent>
        <div className="space-y-6">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-800 dark:text-red-300 whitespace-pre-line">{error}</p>
            </div>
          )}

          <ProfissionalDadosBasicosSection form={form} onFieldChange={setField} />
          <ProfissionalPrescritorSection form={form} onFieldChange={setField} />

          <section className="bg-white dark:bg-neutral-800 rounded-xl border dark:border-neutral-700 p-5 space-y-5">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Comissões</h3>
            <ProfissionalComissaoConsultaBlock
              comissoesConsultaLocal={comissoesConsultaLocal}
              locais={locais}
              locaisDisponiveisConsulta={locaisDisponiveisConsulta}
              onAdd={addComissaoConsultaLocal}
              onRemove={removeComissaoConsultaLocal}
              onUpdate={updateComissaoConsultaLocal}
            />
            <ProfissionalComissaoProcedimentoBlock
              comissoes={comissoes}
              procedures={procedures}
              convenios={convenios}
              onAdd={addComissao}
              onRemove={removeComissao}
              onUpdate={updateComissao}
            />
          </section>

          {!editId && <ProfissionalAcessoSection form={form} onFieldChange={setField} />}

          <div className="flex gap-3 pb-8">
            <button
              type="button"
              onClick={onDone}
              className="flex-1 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={() => void salvar()}
              disabled={saving}
              className="flex-1 py-2.5 rounded-lg text-white text-sm font-medium disabled:opacity-50 inline-flex items-center justify-center gap-2"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Save size={16} />
              {saving ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
