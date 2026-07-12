"use client";

import type { Consulta, ConsultaProcedimento } from "./consultas-types";
import { ProcedimentoAdicionarForm } from "./procedimentos-consulta/ProcedimentoAdicionarForm";
import { ProcedimentosConsultaAlerts } from "./procedimentos-consulta/ProcedimentosConsultaAlerts";
import { ProcedimentosConsultaLista } from "./procedimentos-consulta/ProcedimentosConsultaLista";
import { ProcedimentosConsultaToolbar } from "./procedimentos-consulta/ProcedimentosConsultaToolbar";
import { deveExibirProcedimentosSection } from "./procedimentos-consulta/procedimentos-consulta-utils";
import { useConsultaProcedimentos } from "./procedimentos-consulta/useConsultaProcedimentos";

/** Controles compactos — inclusão/remoção dentro de Notas do atendimento (sem card grande). */
export function ConsultaProcedimentosSection({
  consultaId,
  somenteLeitura,
  procedimentosIniciais = [],
  onChanged,
}: {
  consultaId: number;
  somenteLeitura: boolean;
  procedimentosIniciais?: ConsultaProcedimento[];
  onChanged?: (consulta?: Partial<Consulta>) => void;
}) {
  const {
    itens,
    loading,
    saving,
    showAddForm,
    showManageList,
    procedureId,
    erro,
    avisoTermo,
    opcoesDisponiveis,
    podeAdicionar,
    setProcedureId,
    toggleManageList,
    abrirAddForm,
    fecharAddForm,
    adicionar,
    remover,
  } = useConsultaProcedimentos({ consultaId, procedimentosIniciais, onChanged });

  if (somenteLeitura) return null;

  if (
    !deveExibirProcedimentosSection({
      loading,
      itensCount: itens.length,
      podeAdicionar,
      showAddForm,
      erro,
      avisoTermo,
    })
  ) {
    return null;
  }

  return (
    <div className="mb-4 space-y-3">
      <div className="flex flex-wrap items-center justify-end gap-2">
        <ProcedimentosConsultaToolbar
          itensCount={itens.length}
          showManageList={showManageList}
          podeAdicionar={podeAdicionar}
          saving={saving}
          onToggleManageList={toggleManageList}
          onAbrirAddForm={abrirAddForm}
        />
      </div>

      <ProcedimentosConsultaAlerts erro={erro} avisoTermo={avisoTermo} />

      {showAddForm && (
        <ProcedimentoAdicionarForm
          opcoesDisponiveis={opcoesDisponiveis}
          procedureId={procedureId}
          saving={saving}
          onProcedureChange={setProcedureId}
          onAdicionar={() => void adicionar()}
          onCancel={fecharAddForm}
        />
      )}

      {showManageList && itens.length > 0 && (
        <ProcedimentosConsultaLista
          itens={itens}
          saving={saving}
          onRemover={(item) => void remover(item)}
        />
      )}
    </div>
  );
}
