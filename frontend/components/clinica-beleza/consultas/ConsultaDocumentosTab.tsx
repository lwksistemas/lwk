"use client";

import { DigitarManualModal } from "./DigitarManualModal";
import { UsarTemplateModal } from "./UsarTemplateModal";
import { DocumentoCriarSection } from "./documentos/DocumentoCriarSection";
import { DocumentoListaSection } from "./documentos/DocumentoListaSection";
import { useConsultaDocumentos } from "./documentos/useConsultaDocumentos";

export type { DocumentoAcao, DocumentoTipo } from "./documentos/documentos-types";

/**
 * Seção de documentos clínicos na consulta (receituário, exames, atestado, manual, Memed).
 */
export function ConsultaDocumentosTab({
  consultaId,
  consultaAtiva,
  professionalId,
  onUsarMemed,
  refreshPrescricoes = 0,
}: {
  consultaId: number;
  consultaAtiva: boolean;
  professionalId?: number | null;
  onUsarMemed?: () => void;
  refreshPrescricoes?: number;
}) {
  const {
    openDropdown,
    documentos,
    prescricoesMemed,
    loadingDocs,
    deletingId,
    confirmDeleteId,
    setConfirmDeleteId,
    templateModalTipo,
    setTemplateModalTipo,
    manualModalTipo,
    setManualModalTipo,
    savingManualDoc,
    fetchDocumentos,
    registrarDocumentoCriado,
    handleDelete,
    toggleDropdown,
    handleAcao,
    salvarDocumentoManual,
    atualizarPdfUrlPrescricao,
  } = useConsultaDocumentos(consultaId, refreshPrescricoes);

  return (
    <div className="space-y-5">
      <DocumentoCriarSection
        consultaAtiva={consultaAtiva}
        openDropdown={openDropdown}
        onToggleDropdown={toggleDropdown}
        onAcao={(tipo, acao) => handleAcao(tipo, acao, onUsarMemed)}
      />

      <DocumentoListaSection
        loading={loadingDocs}
        documentos={documentos}
        prescricoesMemed={prescricoesMemed}
        consultaAtiva={consultaAtiva}
        confirmDeleteId={confirmDeleteId}
        deletingId={deletingId}
        onConfirmDelete={setConfirmDeleteId}
        onCancelDelete={() => setConfirmDeleteId(null)}
        onDelete={(id) => void handleDelete(id)}
        onPrescricaoPdfUrl={atualizarPdfUrlPrescricao}
      />

      {templateModalTipo && (
        <UsarTemplateModal
          open={!!templateModalTipo}
          tipo={templateModalTipo}
          consultaId={consultaId}
          professionalId={professionalId ?? undefined}
          onClose={() => setTemplateModalTipo(null)}
          onSuccess={async (created) => {
            setTemplateModalTipo(null);
            if (created) await registrarDocumentoCriado(created);
            else await fetchDocumentos();
          }}
        />
      )}

      {manualModalTipo && (
        <DigitarManualModal
          open={!!manualModalTipo}
          tipo={manualModalTipo}
          saving={savingManualDoc}
          onClose={() => setManualModalTipo(null)}
          onSave={salvarDocumentoManual}
        />
      )}
    </div>
  );
}
