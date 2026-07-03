import { useCallback, useEffect, useMemo, useState } from "react";
import type { PatientQuickOption, PatientQuickRegisterFieldProps } from "./patient-quick-register-types";
import { buildPatientQuickSearchQuery, filterPatientsLocal } from "./patient-quick-register-utils";

export function usePatientQuickRegister({
  patients,
  patientId,
  onSelect,
  onClear,
  onPatientCreated,
  onCreatePatient,
  onSearchPatients,
  disabled = false,
}: PatientQuickRegisterFieldProps) {
  const [nomeNovo, setNomeNovo] = useState("");
  const [telefoneNovo, setTelefoneNovo] = useState("");
  const [cpfNovo, setCpfNovo] = useState("");
  const [criando, setCriando] = useState(false);
  const [erro, setErro] = useState("");
  const [serverResults, setServerResults] = useState<PatientQuickOption[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedCache, setSelectedCache] = useState<PatientQuickOption | null>(null);

  const selecionado =
    selectedCache ||
    patients.find((p) => p.id === patientId) ||
    serverResults.find((p) => p.id === patientId) ||
    null;

  const searchQuery = useMemo(
    () => buildPatientQuickSearchQuery(nomeNovo, telefoneNovo, cpfNovo),
    [nomeNovo, telefoneNovo, cpfNovo],
  );

  const resultados = useMemo(() => {
    if (!searchQuery || patientId) return [];
    if (onSearchPatients) return serverResults;
    return filterPatientsLocal(patients, searchQuery);
  }, [searchQuery, patientId, onSearchPatients, serverResults, patients]);

  useEffect(() => {
    if (!onSearchPatients || patientId || disabled) return;
    if (!searchQuery) {
      setServerResults([]);
      setSearching(false);
      return;
    }
    let cancelled = false;
    setSearching(true);
    const timer = window.setTimeout(() => {
      onSearchPatients(searchQuery)
        .then((rows) => {
          if (!cancelled) setServerResults(Array.isArray(rows) ? rows : []);
        })
        .catch(() => {
          if (!cancelled) setServerResults([]);
        })
        .finally(() => {
          if (!cancelled) setSearching(false);
        });
    }, 300);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [searchQuery, onSearchPatients, patientId, disabled]);

  const handleSelecionar = useCallback(
    (p: PatientQuickOption) => {
      onSelect(p.id);
      setSelectedCache(p);
      setErro("");
    },
    [onSelect],
  );

  const handleTrocar = useCallback(() => {
    onClear();
    setSelectedCache(null);
    setNomeNovo("");
    setTelefoneNovo("");
    setCpfNovo("");
    setServerResults([]);
    setErro("");
  }, [onClear]);

  const handleCriar = useCallback(async () => {
    const nome = nomeNovo.trim();
    if (!nome) {
      setErro("Informe o nome do paciente.");
      return;
    }
    setCriando(true);
    setErro("");
    try {
      const created = await onCreatePatient({
        nome,
        telefone: telefoneNovo.replace(/\D/g, "") ? telefoneNovo : "",
        cpf: cpfNovo.replace(/\D/g, "") ? cpfNovo : "",
      });
      onPatientCreated(created);
      handleSelecionar(created);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao cadastrar paciente.");
    } finally {
      setCriando(false);
    }
  }, [cpfNovo, handleSelecionar, nomeNovo, onCreatePatient, onPatientCreated, telefoneNovo]);

  return {
    selecionado,
    nomeNovo,
    setNomeNovo,
    telefoneNovo,
    setTelefoneNovo,
    cpfNovo,
    setCpfNovo,
    criando,
    erro,
    searchQuery,
    searching,
    resultados,
    handleSelecionar,
    handleTrocar,
    handleCriar,
    disabled,
  };
}
