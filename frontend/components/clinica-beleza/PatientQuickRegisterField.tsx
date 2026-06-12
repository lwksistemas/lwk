"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Search, UserPlus } from "lucide-react";
import { formatCpf, formatTelefone } from "@/lib/format-br";
import { entityName } from "@/lib/clinica-beleza-entities";

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
  /** Busca server-side (nome, telefone, CPF). Quando informado, não filtra lista local completa. */
  onSearchPatients?: (query: string) => Promise<PatientQuickOption[]>;
  disabled?: boolean;
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
  const [busca, setBusca] = useState("");
  const [modoCadastro, setModoCadastro] = useState(false);
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

  const filtrados = useMemo(() => {
    if (onSearchPatients) return serverResults;
    const q = busca.trim().toLowerCase();
    if (!q) return patients.slice(0, 40);
    return patients.filter((p) => {
      const nome = (entityName(p) || "").toLowerCase();
      const tel = (p.telefone || p.phone || "").replace(/\D/g, "");
      const cpf = (p.cpf || "").replace(/\D/g, "");
      const qDigits = q.replace(/\D/g, "");
      return nome.includes(q) || (qDigits && (tel.includes(qDigits) || cpf.includes(qDigits)));
    }).slice(0, 40);
  }, [busca, patients, onSearchPatients, serverResults]);

  useEffect(() => {
    if (!onSearchPatients) return;
    const q = busca.trim();
    if (q.length < 2) {
      setServerResults([]);
      setSearching(false);
      return;
    }
    let cancelled = false;
    setSearching(true);
    const timer = window.setTimeout(() => {
      onSearchPatients(q)
        .then((rows) => {
          if (!cancelled) setServerResults(rows);
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
  }, [busca, onSearchPatients]);

  useEffect(() => {
    if (selecionado) {
      setBusca(entityName(selecionado));
      setModoCadastro(false);
    }
  }, [patientId, selecionado]);

  const abrirCadastroRapido = () => {
    setModoCadastro(true);
    setNomeNovo(busca.trim());
    setTelefoneNovo("");
    setCpfNovo("");
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
      onSelect(created.id);
      setSelectedCache(created);
      setBusca(entityName(created));
      setModoCadastro(false);
      setNomeNovo("");
      setTelefoneNovo("");
      setCpfNovo("");
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao cadastrar paciente.");
    } finally {
      setCriando(false);
    }
  };

  return (
    <div>
      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
        Paciente *
      </label>

      {!modoCadastro ? (
        <>
          <div className="relative mb-2">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={busca}
              onChange={(e) => {
                setBusca(e.target.value);
                if (patientId) onClear();
              }}
              placeholder="Buscar por nome, telefone ou CPF..."
              disabled={disabled}
              className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 focus:ring-2 focus:ring-purple-200 dark:focus:ring-purple-800 outline-none"
            />
          </div>

          {busca.trim() && !patientId && onSearchPatients && busca.trim().length < 2 && (
            <p className="text-xs text-gray-500 mb-2">Digite ao menos 2 caracteres para buscar.</p>
          )}

          {busca.trim() && !patientId && searching && (
            <p className="text-xs text-gray-500 mb-2">Buscando...</p>
          )}

          {busca.trim() && !patientId && !searching && filtrados.length > 0 && (
            <div className="border border-gray-200 dark:border-neutral-600 rounded-lg overflow-hidden mb-2 max-h-36 overflow-y-auto">
              {filtrados.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    onSelect(p.id);
                    setSelectedCache(p);
                    setBusca(entityName(p));
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-neutral-700 border-b last:border-b-0 border-gray-100 dark:border-neutral-700"
                >
                  <span className="font-medium">{entityName(p)}</span>
                  {(p.telefone || p.phone) && (
                    <span className="ml-2 text-xs text-gray-500">{formatTelefone(p.telefone || p.phone)}</span>
                  )}
                </button>
              ))}
            </div>
          )}

          {busca.trim() && !patientId && !searching && filtrados.length === 0 && busca.trim().length >= (onSearchPatients ? 2 : 1) && (
            <p className="text-xs text-gray-500 mb-2">Nenhum paciente encontrado.</p>
          )}

          {!patientId && (
            <button
              type="button"
              onClick={abrirCadastroRapido}
              disabled={disabled}
              className="flex items-center gap-1.5 text-xs font-medium text-purple-700 dark:text-purple-300 hover:underline mb-2"
            >
              <UserPlus size={14} />
              Cadastro rápido (nome, telefone, CPF)
            </button>
          )}

          {selecionado && (
            <div className="flex items-center gap-2 px-3 py-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <span className="text-sm text-green-700 dark:text-green-400">
                ✓ <strong>{entityName(selecionado)}</strong>
              </span>
              <button
                type="button"
                onClick={() => {
                  onClear();
                  setBusca("");
                  setSelectedCache(null);
                }}
                className="ml-auto text-xs text-gray-400 hover:text-red-500"
              >
                Trocar
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-900/10 p-3 space-y-2">
          <p className="text-xs font-medium text-purple-800 dark:text-purple-300">Cadastro rápido</p>
          <input
            type="text"
            value={nomeNovo}
            onChange={(e) => setNomeNovo(e.target.value)}
            placeholder="Nome *"
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700"
            autoFocus
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <input
              type="tel"
              value={telefoneNovo}
              onChange={(e) => setTelefoneNovo(formatTelefone(e.target.value))}
              placeholder="Telefone"
              className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700"
            />
            <input
              type="text"
              value={cpfNovo}
              onChange={(e) => setCpfNovo(formatCpf(e.target.value))}
              placeholder="CPF"
              className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700"
            />
          </div>
          {erro && <p className="text-xs text-red-600 dark:text-red-400">{erro}</p>}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleCriar}
              disabled={criando}
              className="px-3 py-1.5 text-xs font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              {criando ? "Salvando..." : "Salvar paciente"}
            </button>
            <button
              type="button"
              onClick={() => {
                setModoCadastro(false);
                setErro("");
              }}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
