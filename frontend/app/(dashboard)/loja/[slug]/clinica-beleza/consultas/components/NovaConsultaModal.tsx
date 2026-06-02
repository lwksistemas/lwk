"use client";

import { useEffect, useMemo, useState } from "react";
import { X, Search } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";
import type { Consulta } from "./consultas-types";

interface Option {
  id: number;
  nome: string;
}

/**
 * Abre uma consulta avulsa (sem agendamento prévio na agenda) selecionando um
 * cliente já cadastrado, o profissional e o procedimento. A consulta é criada
 * em "Em atendimento", liberando imediatamente o receituário/exames.
 */
export function NovaConsultaModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (consulta: Consulta) => void;
}) {
  const [patients, setPatients] = useState<Option[]>([]);
  const [professionals, setProfessionals] = useState<Option[]>([]);
  const [procedures, setProcedures] = useState<Option[]>([]);
  const [loadingData, setLoadingData] = useState(false);

  const [busca, setBusca] = useState("");
  const [patientId, setPatientId] = useState<number | "">("");
  const [professionalId, setProfessionalId] = useState<number | "">("");
  const [procedureId, setProcedureId] = useState<number | "">("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  useEffect(() => {
    if (!open) return;
    setBusca("");
    setPatientId("");
    setProfessionalId("");
    setProcedureId("");
    setErro("");
    setLoadingData(true);
    (async () => {
      try {
        const [pac, prof, proc] = await Promise.all([
          ClinicaBelezaAPI.get<Option[]>("/patients/"),
          ClinicaBelezaAPI.get<Option[]>("/professionals/"),
          ClinicaBelezaAPI.get<Option[]>("/procedures/"),
        ]);
        const ativos = (arr: unknown) => (Array.isArray(arr) ? (arr as Option[]) : []);
        setPatients(ativos(pac));
        const profList = ativos(prof);
        const procList = ativos(proc);
        setProfessionals(profList);
        setProcedures(procList);
        if (profList.length === 1) setProfessionalId(profList[0].id);
        if (procList.length === 1) setProcedureId(procList[0].id);
      } catch (e) {
        logger.warn("Erro ao carregar dados para nova consulta:", e);
        setErro("Não foi possível carregar os cadastros. Tente novamente.");
      } finally {
        setLoadingData(false);
      }
    })();
  }, [open]);

  const pacientesFiltrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    const base = q ? patients.filter((p) => (p.nome || "").toLowerCase().includes(q)) : patients;
    return base.slice(0, 50);
  }, [busca, patients]);

  // Seleciona automaticamente quando a busca deixa apenas um cliente, evitando o
  // erro comum de digitar e esquecer de clicar no nome na lista.
  useEffect(() => {
    if (pacientesFiltrados.length === 1) {
      setPatientId(pacientesFiltrados[0].id);
    }
  }, [pacientesFiltrados]);

  const clienteSelecionado = useMemo(
    () => patients.find((p) => p.id === patientId) || null,
    [patients, patientId],
  );

  const criar = async () => {
    if (!patientId || !professionalId || !procedureId) {
      setErro("Selecione o cliente, o profissional e o procedimento.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      const consulta = await ClinicaBelezaAPI.consultas.criar({
        patient: Number(patientId),
        professional: Number(professionalId),
        procedure: Number(procedureId),
      });
      onCreated(consulta as Consulta);
    } catch (e: unknown) {
      logger.warn("Erro ao abrir consulta avulsa:", e);
      setErro(e instanceof Error ? e.message : "Erro ao abrir a consulta.");
    } finally {
      setSalvando(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Nova consulta</h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
            <X size={18} />
          </button>
        </div>
        <div className="p-4 space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Abre uma consulta direto pelo cadastro do cliente, sem precisar passar pela Agenda.
            O profissional inicia o atendimento quando estiver pronto.
          </p>

          {loadingData ? (
            <div className="text-center py-8 text-gray-500 text-sm">Carregando cadastros...</div>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">Cliente</label>
                <div className="relative mb-2">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    value={busca}
                    onChange={(e) => setBusca(e.target.value)}
                    placeholder="Buscar cliente pelo nome..."
                    className="w-full pl-9 pr-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                  />
                </div>
                <select
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value ? Number(e.target.value) : "")}
                  size={5}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                >
                  {pacientesFiltrados.length === 0 ? (
                    <option value="" disabled>Nenhum cliente encontrado</option>
                  ) : (
                    pacientesFiltrados.map((p) => (
                      <option key={p.id} value={p.id}>{p.nome}</option>
                    ))
                  )}
                </select>
                {clienteSelecionado ? (
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    Cliente selecionado: <strong>{clienteSelecionado.nome}</strong>
                  </p>
                ) : (
                  <p className="text-xs text-gray-400 mt-1">
                    Clique no nome para selecionar. O cliente precisa estar cadastrado em Pacientes.
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Profissional</label>
                <select
                  value={professionalId}
                  onChange={(e) => setProfessionalId(e.target.value ? Number(e.target.value) : "")}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                >
                  <option value="">Selecione...</option>
                  {professionals.map((p) => (
                    <option key={p.id} value={p.id}>{p.nome}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Procedimento</label>
                <select
                  value={procedureId}
                  onChange={(e) => setProcedureId(e.target.value ? Number(e.target.value) : "")}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                >
                  <option value="">Selecione...</option>
                  {procedures.map((p) => (
                    <option key={p.id} value={p.id}>{p.nome}</option>
                  ))}
                </select>
              </div>
            </>
          )}

          {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}

          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600">
              Cancelar
            </button>
            <button
              type="button"
              onClick={criar}
              disabled={salvando || loadingData}
              className="flex-1 py-2 rounded-lg text-white disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              {salvando ? "Abrindo..." : "Abrir consulta"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
