"use client";

/**
 * Nova Consulta — Página dedicada (full page)
 */

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ConvenioSelect } from "@/components/clinica-beleza/ConvenioSelect";
import { PatientSearchField } from "@/components/clinica-beleza/PatientSearchField";
import { ProcedureMultiSelect } from "@/components/clinica-beleza/ProcedureMultiSelect";
import { useConvenioPrecos } from "@/hooks/clinica-beleza/useConvenioPrecos";
import { useConveniosList } from "@/hooks/clinica-beleza/useConveniosList";
import { ClinicaBelezaAPI, type LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import { entityName } from "@/lib/clinica-beleza-entities";
import { logger } from "@/lib/logger";

interface Option {
  id: number;
  nome: string;
  name?: string;
  duracao_minutos?: number;
  preco?: number;
  convenio?: number | null;
}

export default function NovaConsultaPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const [patients, setPatients] = useState<Option[]>([]);
  const [professionals, setProfessionals] = useState<Option[]>([]);
  const [procedures, setProcedures] = useState<Option[]>([]);
  const [locais, setLocais] = useState<LocalAtendimentoItem[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  const [busca, setBusca] = useState("");
  const [patientId, setPatientId] = useState<number | "">("");
  const [professionalId, setProfessionalId] = useState<number | "">("");
  const [convenioId, setConvenioId] = useState<number | "">("");
  const [selectedProcedures, setSelectedProcedures] = useState<number[]>([]);
  const [localAtendimentoId, setLocalAtendimentoId] = useState<number | "">("");
  const [valorConsulta, setValorConsulta] = useState<string>("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  const convenios = useConveniosList();
  const precosMap = useConvenioPrecos(convenioId);

  const voltar = useCallback(() => {
    router.push(`/loja/${slug}/clinica-beleza/consultas`);
  }, [router, slug]);

  useEffect(() => {
    (async () => {
      try {
        const [pac, prof, proc, locaisRes] = await Promise.all([
          ClinicaBelezaAPI.get<Option[]>("/patients/"),
          ClinicaBelezaAPI.professionals.list(),
          ClinicaBelezaAPI.get<Option[]>("/procedures/"),
          ClinicaBelezaAPI.locaisAtendimento.list(),
        ]);
        const ativos = (arr: unknown) => (Array.isArray(arr) ? (arr as Option[]) : []);
        setPatients(ativos(pac));
        const profList = ativos(prof);
        setProfessionals(profList);
        setProcedures(ativos(proc));
        setLocais(Array.isArray(locaisRes) ? locaisRes : []);
        if (profList.length === 1) setProfessionalId(profList[0].id);
      } catch (e) {
        logger.warn("Erro ao carregar dados para nova consulta:", e);
        setErro("Não foi possível carregar os cadastros. Tente novamente.");
      } finally {
        setLoadingData(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!patientId) return;
    const paciente = patients.find((p) => p.id === patientId);
    setConvenioId(paciente?.convenio ?? "");
  }, [patientId, patients]);

  const adicionarProcedimento = (id: number) => {
    if (id && !selectedProcedures.includes(id)) {
      setSelectedProcedures((prev) => [...prev, id]);
    }
  };

  const removerProcedimento = (id: number) => {
    setSelectedProcedures((prev) => prev.filter((p) => p !== id));
  };

  const handleLocalChange = (id: number | "") => {
    setLocalAtendimentoId(id);
    if (id) {
      const local = locais.find((l) => l.id === id);
      if (local) {
        setValorConsulta(String(Number(local.valor_consulta)));
      }
    } else {
      setValorConsulta("");
    }
  };

  const criar = async () => {
    if (!patientId || !professionalId || selectedProcedures.length === 0) {
      setErro("Selecione o cliente, o profissional e pelo menos um procedimento.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      const payload: {
        patient: number;
        professional: number;
        procedures_ids: number[];
        local_atendimento?: number;
        valor_consulta?: number | string;
        convenio?: number;
      } = {
        patient: Number(patientId),
        professional: Number(professionalId),
        procedures_ids: selectedProcedures,
      };
      if (convenioId) {
        payload.convenio = Number(convenioId);
      }
      if (localAtendimentoId) {
        payload.local_atendimento = Number(localAtendimentoId);
      }
      if (valorConsulta) {
        payload.valor_consulta = valorConsulta;
      }
      await ClinicaBelezaAPI.consultas.criar(payload);
      router.push(`/loja/${slug}/clinica-beleza/consultas`);
    } catch (e: unknown) {
      logger.warn("Erro ao abrir consulta avulsa:", e);
      setErro(e instanceof Error ? e.message : "Erro ao abrir a consulta.");
    } finally {
      setSalvando(false);
    }
  };

  const patientOptions = patients.map((p) => ({
    id: p.id,
    nome: p.nome || entityName(p),
    convenio: p.convenio,
  }));

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Nova consulta"
        subtitle="Abra um atendimento direto pelo cadastro do cliente"
        backHref={`/loja/${slug}/clinica-beleza/consultas`}
      />
      <ClinicaBelezaPageContent>
        <ClinicaBelezaPanel className="p-6 md:p-8">
            {loadingData ? (
              <div className="text-center py-16 text-gray-500 text-sm">Carregando cadastros...</div>
            ) : (
              <div className="space-y-6">
                <PatientSearchField
                  patients={patientOptions}
                  busca={busca}
                  onBuscaChange={setBusca}
                  patientId={patientId}
                  onSelect={setPatientId}
                  onClear={() => setPatientId("")}
                />

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Profissional *
                  </label>
                  <select
                    value={professionalId}
                    onChange={(e) => setProfessionalId(e.target.value ? Number(e.target.value) : "")}
                    className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors"
                  >
                    <option value="">Selecione...</option>
                    {professionals.map((p) => (
                      <option key={p.id} value={p.id}>{p.nome || entityName(p)}</option>
                    ))}
                  </select>
                </div>

                <ConvenioSelect
                  convenios={convenios}
                  value={convenioId}
                  onChange={setConvenioId}
                />

                {locais.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Local de Atendimento
                    </label>
                    <select
                      value={localAtendimentoId}
                      onChange={(e) => handleLocalChange(e.target.value ? Number(e.target.value) : "")}
                      className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors"
                    >
                      <option value="">Selecione o local...</option>
                      {locais.map((l) => (
                        <option key={l.id} value={l.id}>
                          {l.nome} — R$ {Number(l.valor_consulta).toFixed(2)}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {locais.length > 0 && localAtendimentoId && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Valor da Consulta (R$)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={valorConsulta}
                      onChange={(e) => setValorConsulta(e.target.value)}
                      className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors"
                      placeholder="0.00"
                    />
                    <p className="text-xs text-gray-400 mt-1.5">
                      Preenchido pelo local selecionado. Pode ser alterado manualmente.
                    </p>
                  </div>
                )}

                <ProcedureMultiSelect
                  procedures={procedures}
                  selectedIds={selectedProcedures}
                  onAdd={adicionarProcedimento}
                  onRemove={removerProcedimento}
                  convenioId={convenioId}
                  precosMap={precosMap}
                />

                {erro && (
                  <div className="px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>
                  </div>
                )}

                <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-neutral-700">
                  <button
                    type="button"
                    onClick={voltar}
                    className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
                  >
                    <ArrowLeft size={16} />
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={criar}
                    disabled={salvando}
                    className="flex-1 py-3 rounded-lg text-white text-sm font-medium disabled:opacity-50 hover:opacity-90 transition-opacity"
                    style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                  >
                    {salvando ? "Abrindo consulta..." : "Abrir consulta"}
                  </button>
                </div>
              </div>
            )}
          </ClinicaBelezaPanel>
      </ClinicaBelezaPageContent>
    </>
  );
}
