"use client";

import { formatCpf, formatTelefone } from "@/lib/format-br";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { entityName } from "@/lib/clinica-beleza-entities";
import type { PatientQuickRegisterFieldProps } from "./patient-quick-register-types";
import { usePatientQuickRegister } from "./usePatientQuickRegister";

const inputClass =
  "w-full px-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 min-h-[44px]";

export function PatientQuickRegisterField(props: PatientQuickRegisterFieldProps) {
  const {
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
  } = usePatientQuickRegister(props);

  return (
    <div>
      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Paciente *</label>

      {selecionado ? (
        <div className="flex items-center gap-3 px-3 py-2.5 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <PacienteAvatar fotoUrl={selecionado.foto_url} name={entityName(selecionado)} size="sm" />
          <div className="min-w-0 flex-1">
            <p className="text-sm text-green-700 dark:text-green-400 truncate">
              ✓ <strong>{entityName(selecionado)}</strong>
            </p>
            {(selecionado.telefone || selecionado.phone) && (
              <p className="text-xs text-green-600/80 dark:text-green-300/80">
                {formatTelefone(selecionado.telefone || selecionado.phone)}
              </p>
            )}
          </div>
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
            Cadastro rápido — ao digitar, busca no cadastro: nome desde a 1ª letra (Lu, Lui…), telefone/CPF com 3+
            dígitos.
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
                  className="w-full text-left px-3 py-2 text-sm hover:bg-purple-50 dark:hover:bg-purple-900/20 border-b last:border-b-0 border-gray-100 dark:border-neutral-700 flex items-center gap-2.5"
                >
                  <PacienteAvatar fotoUrl={p.foto_url} name={entityName(p)} size="sm" />
                  <span className="min-w-0 flex-1">
                    <span className="font-medium block truncate">{entityName(p)}</span>
                    <span className="text-xs text-gray-500">
                      {(p.telefone || p.phone) && formatTelefone(p.telefone || p.phone)}
                      {p.cpf && (
                        <>
                          {p.telefone || p.phone ? " · " : ""}
                          {formatCpf(p.cpf)}
                        </>
                      )}
                    </span>
                  </span>
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
            onClick={() => void handleCriar()}
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
