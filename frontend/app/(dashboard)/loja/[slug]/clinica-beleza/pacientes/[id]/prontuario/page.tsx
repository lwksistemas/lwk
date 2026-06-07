"use client";

/**
 * Prontuário do Paciente — Clínica da Beleza
 * Visualização do prontuário completo organizado por seções (tabs).
 * Tabs: Receitas | Exames | Atestados | Atendimento | Anamnese | Evolução
 *
 * Cada tab carrega dados da API: GET /patients/<id>/prontuario/?secao=X
 */

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Pill,
  FlaskConical,
  FileCheck,
  FolderOpen,
  FileText,
  Activity,
  Printer,
} from "lucide-react";
import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import {
  ClinicaBelezaAPI,
  clinicaBelezaFetch,
  type ProntuarioData,
  type ProntuarioDocItem,
  type ProntuarioEvolucaoItem,
} from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";

/** Mapeamento de tab para seção da API */
type ProntuarioTabId =
  | "receituario"
  | "pedido_exame"
  | "atestado"
  | "documento_personalizado"
  | "anamnese"
  | "evolucao";

interface TabDef {
  id: ProntuarioTabId;
  label: string;
  icon: typeof Pill;
}

const TABS: TabDef[] = [
  { id: "receituario", label: "Receitas", icon: Pill },
  { id: "pedido_exame", label: "Exames", icon: FlaskConical },
  { id: "atestado", label: "Atestados", icon: FileCheck },
  { id: "documento_personalizado", label: "Atendimento", icon: FolderOpen },
  { id: "anamnese", label: "Anamnese", icon: FileText },
  { id: "evolucao", label: "Evolução", icon: Activity },
];

export default function ProntuarioPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const patientId = Number(params.id);

  const [activeTab, setActiveTab] = useState<ProntuarioTabId>("receituario");
  const [data, setData] = useState<ProntuarioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [patientName, setPatientName] = useState("");

  /**
   * Carrega dados do prontuário por seção.
   * GET /clinica-beleza/patients/<id>/prontuario/?secao=X
   * Quando secao é passada, o backend retorna apenas os dados daquela seção.
   */
  const loadProntuario = useCallback(
    async (secao?: string) => {
      setLoading(true);
      try {
        const result = await ClinicaBelezaAPI.prontuario.get(patientId, secao);
        setData(result);
      } catch (e) {
        logger.warn("Erro ao carregar prontuário:", e);
        setData(null);
      } finally {
        setLoading(false);
      }
    },
    [patientId]
  );

  /** Carrega nome do paciente para exibir no header */
  const loadPatientName = useCallback(async () => {
    try {
      const patient = await ClinicaBelezaAPI.get<{ name?: string; nome?: string }>(
        `/patients/${patientId}/`
      );
      setPatientName(patient.name || patient.nome || "Paciente");
    } catch {
      setPatientName("Paciente");
    }
  }, [patientId]);

  // Carrega dados iniciais: nome do paciente e primeira seção
  useEffect(() => {
    loadPatientName();
    loadProntuario(activeTab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadPatientName, patientId]);

  /**
   * Ao trocar de tab, carrega a seção correspondente da API.
   * Isso garante que cada tab reflete os dados mais recentes do backend.
   */
  const handleTabChange = (tabId: ProntuarioTabId) => {
    setActiveTab(tabId);
    loadProntuario(tabId);
  };

  const voltarPacientes = () => {
    router.push(`/loja/${slug}/clinica-beleza/pacientes`);
  };

  /**
   * Abre PDF da seção ativa em nova aba.
   * URL: /clinica-beleza/patients/<id>/prontuario/pdf/?secao=X
   */
  const handlePrintSecao = () => {
    const url = ClinicaBelezaAPI.prontuario.pdfUrl(patientId, activeTab);
    window.open(url, "_blank");
  };

  /**
   * Abre PDF do prontuário completo em nova aba.
   * URL: /clinica-beleza/patients/<id>/prontuario/pdf/
   */
  const handlePrintCompleto = () => {
    const url = ClinicaBelezaAPI.prontuario.pdfUrl(patientId);
    window.open(url, "_blank");
  };

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={`Prontuário — ${patientName}`}
        subtitle="Histórico clínico completo do paciente"
        backHref={`/loja/${slug}/clinica-beleza/pacientes`}
        icon={FileText}
      />

      <div className="min-h-full bg-[#f7f2f4] dark:bg-gray-950 flex flex-col">
        {/* Header com voltar + tabs */}
        <div className="px-4 md:px-6 pt-2 pb-4 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80">
          <button
            type="button"
            onClick={voltarPacientes}
            className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-3"
          >
            <ArrowLeft size={16} />
            Voltar aos clientes
          </button>

          {/* Tabs de navegação — cada uma dispara GET /patients/<id>/prontuario/?secao=X */}
          <div className="flex flex-wrap items-center gap-2">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => handleTabChange(id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === id
                    ? "text-white"
                    : "bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700"
                }`}
                style={activeTab === id ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
              >
                <Icon size={16} />
                {label}
              </button>
            ))}

            {/* Separador visual */}
            <div className="hidden sm:block w-px h-6 bg-gray-300 dark:bg-neutral-600 mx-1" />

            {/* Botão Imprimir Seção — PDF de todos os docs da seção ativa */}
            <button
              type="button"
              onClick={() => handlePrintSecao()}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700 transition-colors"
              title="Imprimir todos os documentos desta seção"
            >
              <Printer size={16} />
              <span className="hidden md:inline">Imprimir Seção</span>
            </button>

            {/* Botão Imprimir Prontuário Completo — PDF de todas as seções */}
            <button
              type="button"
              onClick={() => handlePrintCompleto()}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white transition-colors"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
              title="Imprimir prontuário completo do paciente"
            >
              <Printer size={16} />
              <span className="hidden md:inline">Imprimir Completo</span>
            </button>
          </div>
        </div>

        {/* Conteúdo da tab ativa */}
        <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
          {loading ? (
            <div className="text-center py-16 text-gray-500 dark:text-gray-400">
              Carregando prontuário...
            </div>
          ) : !data ? (
            <ClinicaBelezaPanel className="p-12 text-center text-gray-500 dark:text-gray-400 text-sm">
              Não foi possível carregar o prontuário. Tente novamente.
            </ClinicaBelezaPanel>
          ) : (
            <ProntuarioTabContent data={data} activeTab={activeTab} />
          )}
        </div>
      </div>
    </>
  );
}

/** Renderiza o conteúdo de acordo com a tab ativa */
function ProntuarioTabContent({
  data,
  activeTab,
}: {
  data: ProntuarioData;
  activeTab: ProntuarioTabId;
}) {
  if (activeTab === "anamnese") {
    return <AnamneseSection anamnese={data.anamnese} />;
  }

  if (activeTab === "evolucao") {
    return <EvolucaoSection evolucoes={data.evolucao} />;
  }

  // Receitas, Exames, Atestados, Atendimento (documento_personalizado)
  const docs: ProntuarioDocItem[] = data[activeTab] || [];
  if (docs.length === 0) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        Nenhum registro encontrado nesta seção.
      </ClinicaBelezaPanel>
    );
  }

  return (
    <div className="space-y-4">
      {docs.map((doc) => (
        <DocumentoCard key={`${doc.source}-${doc.id}`} doc={doc} />
      ))}
    </div>
  );
}

/** Card de documento individual — mostra data, profissional, consulta e conteúdo */
function DocumentoCard({ doc }: { doc: ProntuarioDocItem }) {
  const [printing, setPrinting] = useState(false);

  /**
   * Abre PDF individual do documento em nova aba.
   * Para documentos internos (source=documento_clinico): busca via API autenticada e abre blob.
   * Para documentos Memed com pdf_url externo: abre diretamente.
   */
  const handlePrintDocument = async () => {
    if (printing) return;

    if (doc.source === "memed") {
      setPrinting(true);
      try {
        const { abrirPdfPrescricaoMemed } = await import("@/lib/memed-prescricao-pdf");
        await abrirPdfPrescricaoMemed({ id: doc.id, pdf_url: doc.pdf_url });
      } catch (e) {
        logger.warn("Erro ao imprimir prescrição Memed:", e);
        throw e;
      } finally {
        setPrinting(false);
      }
      return;
    }

    // Documentos internos: fetch autenticado → blob → nova aba
    if (doc.source === "documento_clinico") {
      setPrinting(true);
      try {
        const response = await clinicaBelezaFetch(`/documentos/${doc.id}/pdf/`);
        if (!response.ok) {
          logger.warn("Erro ao gerar PDF do documento:", response.status);
          return;
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        window.open(url, "_blank");
        setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
      } catch (e) {
        logger.warn("Erro ao imprimir documento:", e);
      } finally {
        setPrinting(false);
      }
    }
  };

  return (
    <ClinicaBelezaPanel className="p-5">
      <div className="flex items-start justify-between gap-4 mb-2">
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {doc.titulo || tipoLabel(doc.tipo)}
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {doc.professional_name && <span>{doc.professional_name} · </span>}
            {doc.created_at ? formatDate(doc.created_at) : "—"}
            {doc.consulta_id && (
              <span className="ml-2">Consulta #{doc.consulta_id}</span>
            )}
            {doc.source === "memed" && (
              <span className="ml-2 px-1.5 py-0.5 rounded text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                Memed
              </span>
            )}
          </p>
        </div>
        {/* Botão Imprimir — gera PDF individual em nova aba */}
        <button
          type="button"
          onClick={handlePrintDocument}
          disabled={printing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50"
          title="Imprimir documento (PDF)"
        >
          <Printer size={14} />
          {printing ? "Gerando..." : "Imprimir"}
        </button>
      </div>
      <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
        {doc.conteudo}
      </div>
    </ClinicaBelezaPanel>
  );
}

/** Seção de Anamnese */
function AnamneseSection({ anamnese }: { anamnese: ProntuarioData["anamnese"] }) {
  if (!anamnese) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        Nenhuma anamnese registrada para este paciente.
      </ClinicaBelezaPanel>
    );
  }

  const fields = [
    { label: "Queixa Principal", value: anamnese.queixa_principal },
    { label: "Histórico Médico", value: anamnese.historico_medico },
    { label: "Medicamentos em Uso", value: anamnese.medicamentos_uso },
    { label: "Alergias", value: anamnese.alergias },
    { label: "Tipo de Pele", value: anamnese.tipo_pele },
    { label: "Observações", value: anamnese.observacoes },
  ].filter((f) => f.value);

  if (fields.length === 0) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        Anamnese sem dados preenchidos.
      </ClinicaBelezaPanel>
    );
  }

  return (
    <ClinicaBelezaPanel className="p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Anamnese
        </h3>
        {anamnese.updated_at && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Atualizado em {formatDate(anamnese.updated_at)}
          </span>
        )}
      </div>
      <div className="space-y-4">
        {fields.map(({ label, value }) => (
          <div key={label}>
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
              {label}
            </p>
            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
              {value}
            </p>
          </div>
        ))}
      </div>
    </ClinicaBelezaPanel>
  );
}

/** Seção de Evolução */
function EvolucaoSection({ evolucoes }: { evolucoes: ProntuarioEvolucaoItem[] }) {
  if (!evolucoes || evolucoes.length === 0) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        Nenhuma evolução registrada para este paciente.
      </ClinicaBelezaPanel>
    );
  }

  return (
    <div className="space-y-4">
      {evolucoes.map((evo) => (
        <ClinicaBelezaPanel key={evo.id} className="p-5">
          <div className="flex items-start justify-between gap-4 mb-2">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Evolução
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {evo.professional_name && <span>{evo.professional_name} · </span>}
                {evo.created_at ? formatDate(evo.created_at) : "—"}
                {evo.consulta_id && (
                  <span className="ml-2">Consulta #{evo.consulta_id}</span>
                )}
              </p>
            </div>
          </div>
          <div className="space-y-3">
            {evo.descricao && (
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-0.5">
                  Descrição
                </p>
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {evo.descricao}
                </p>
              </div>
            )}
            {evo.procedimento_realizado && (
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-0.5">
                  Procedimento Realizado
                </p>
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {evo.procedimento_realizado}
                </p>
              </div>
            )}
            {evo.produtos_utilizados && (
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-0.5">
                  Produtos Utilizados
                </p>
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {evo.produtos_utilizados}
                </p>
              </div>
            )}
            {evo.orientacoes && (
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-0.5">
                  Orientações
                </p>
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {evo.orientacoes}
                </p>
              </div>
            )}
          </div>
        </ClinicaBelezaPanel>
      ))}
    </div>
  );
}

/** Helpers */
function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

function tipoLabel(tipo: string): string {
  const labels: Record<string, string> = {
    receituario: "Receituário",
    pedido_exame: "Pedido de Exame",
    atestado: "Atestado",
    documento_personalizado: "Documento",
  };
  return labels[tipo] || tipo;
}
