"use client";

import { useEffect, useMemo, useState } from "react";
import { formatCpf, formatTelefone } from "@/lib/format-br";
import { entityName, matchesPatientSearchQuery } from "@/lib/clinica-beleza-entities";

export interface PatientQuickOption {
  id: number;
  nome?: string;
  name?: string;
  telefone?: string;
  phone?: string;
  cpf?: string;
  convenio?: number | null;
}

interface Props {
  patients: PatientQuickOption[];
  patientId: number | "";
  onSelect: (id: number) => void;
  onClear: () => void;
  onPatientCreated: (patient: PatientQuickOption) => void;
  onCreatePatient: (data: { nome: string; telefone: string; cpf: string }) => Promise<PatientQuickOption>;
  /** Busca server-side (nome, telefone, CPF). */
  onSearchPatients?: (query: string) => Promise<PatientQuickOption[]>;
  disabled?: boolean;
}

function buildSearchQuery(nome: string, telefone: string, cpf: string): string {
  const cpfDigits = cpf.replace(/\D/g, "");
  const telDigits = telefone.replace(/\D/g, "");
  const nomeTrim = nome.trim();
  if (cpfDigits.length >= 3) return cpfDigits;
  if (telDigits.length >= 3) return telDigits;
  if (nomeTrim.length >= 1) return nomeTrim;
  return "";
}

export function PatientQuickRegisterField({
  patients,
  patientId,
  onSelect,
  onClear,
  onPatientCreated,
  onCreatePatient,
  onSearchPatients,
  disabled = false,
}: Props) {
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
    () => buildSearchQuery(nomeNovo, telefoneNovo, cpfNovo),
    [nomeNovo, telefoneNovo, cpfNovo],
  );

  const resultados = useMemo(() => {
    if (!searchQuery || patientId) return [];
    if (onSearchPatients) return serverResults;
    return patients.filter((p) => matchesPatientSearchQuery(p, searchQuery)).slice(0, 40);
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

  const handleSelecionar = (p: PatientQuickOption) => {
    onSelect(p.id);
    setSelectedCache(p);
    setErro("");
  };

  const handleTrocar = () => {
    onClear();
    setSelectedCache(null);
    setNomeNovo("");
    setTelefoneNovo("");
    setCpfNovo("");
    setServerResults([]);
    setErro("");
  };

  const handleCriar = async () => {
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
  };

  const inputClass =
    "w-full px-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 min-h-[44px]";

  return (
    <div>
      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
        Paciente *
      </label>

      {selecionado ? (
        <div className="flex items-center gap-2 px-3 py-2.5 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <span className="text-sm text-green-700 dark:text-green-400">
            ✓ <strong>{entityName(selecionado)}</strong>
            {(selecionado.telefone || selecionado.phone) && (
              <span className="ml-2 font-normal text-green-600/80 dark:text-green-300/80">
                {formatTelefone(selecionado.telefone || selecionado.phone)}
              </span>
            )}
          </span>
          <button
            type="button"
            onClick={handleTrocar}
            disabled={disabled}
            className="ml-auto text-xs text-gray-500 hover:text-red-500 shrink-0"
          >
            Trocar
          </button>
        </div>
      ) : (
        <div className="rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50/40 dark:bg-purple-900/10 p-3 space-y-2">
          <p className="text-xs text-purple-800 dark:text-purple-300">
            Cadastro rápido — ao digitar, busca no cadastro: nome desde a 1ª letra (Lu, Lui…), telefone/CPF com 3+ dígitos.
          </p>
          <input
            type="text"
            value={nomeNovo}
            onChange={(e) => setNomeNovo(e.target.value)}
            placeholder="Nome *"
            disabled={disabled}
            className={inputClass}
            autoFocus
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <input
              type="tel"
              value={telefoneNovo}
              onChange={(e) => setTelefoneNovo(formatTelefone(e.target.value))}
              placeholder="Telefone"
              disabled={disabled}
              className={inputClass}
            />
            <input
              type="text"
              value={cpfNovo}
              onChange={(e) => setCpfNovo(formatCpf(e.target.value))}
              placeholder="CPF"
              disabled={disabled}
              className={inputClass}
            />
          </div>

          {searchQuery && searching && (
            <p className="text-xs text-gray-500 dark:text-gray-400">Buscando no cadastro...</p>
          )}

          {searchQuery && !searching && resultados.length > 0 && (
            <div className="border border-gray-200 dark:border-neutral-600 rounded-lg overflow-hidden max-h-40 overflow-y-auto bg-white dark:bg-neutral-800">
              <p className="px-3 py-1.5 text-[11px] font-medium text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-neutral-900/50 border-b border-gray-100 dark:border-neutral-700">
                Pacientes encontrados — selecione ou cadastre novo abaixo
              </p>
              {resultados.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleSelecionar(p)}
                  disabled={disabled}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-purple-50 dark:hover:bg-purple-900/20 border-b last:border-b-0 border-gray-100 dark:border-neutral-700"
                >
                  <span className="font-medium">{entityName(p)}</span>
                  {(p.telefone || p.phone) && (
                    <span className="ml-2 text-xs text-gray-500">
                      {formatTelefone(p.telefone || p.phone)}
                    </span>
                  )}
                  {p.cpf && (
                    <span className="ml-2 text-xs text-gray-500">{formatCpf(p.cpf)}</span>
                  )}
                </button>
              ))}
            </div>
          )}

          {searchQuery && !searching && resultados.length === 0 && (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Nenhum paciente no cadastro — preencha e salve como novo.
            </p>
          )}

          {erro && <p className="text-xs text-red-600 dark:text-red-400">{erro}</p>}

          <button
            type="button"
            onClick={handleCriar}
            disabled={disabled || criando || !nomeNovo.trim()}
            className="w-full sm:w-auto px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {criando ? "Salvando..." : "Salvar novo paciente"}
          </button>
        </div>
      )}
    </div>
  );
}
