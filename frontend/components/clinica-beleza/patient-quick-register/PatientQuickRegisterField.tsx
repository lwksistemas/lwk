"use client";

import { CheckCircle2, Plus, Search } from "lucide-react";
import { formatCpf, formatTelefone } from "@/lib/format-br";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { entityName } from "@/lib/clinica-beleza-entities";
import { cbPrimaryAlpha } from "@/lib/clinica-beleza-theme-utils";
import type { PatientQuickRegisterFieldProps } from "./patient-quick-register-types";
import { usePatientQuickRegister } from "./usePatientQuickRegister";

const inputClass =
  "w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 min-h-[44px]";

export function PatientQuickRegisterField(props: PatientQuickRegisterFieldProps) {
  const theme = useClinicaBelezaTheme();
  const {
    selecionado,
    nomeNovo,
    setNomeNovo,
    telefoneNovo,
    setTelefoneNovo,
    cpfNovo,
    setCpfNovo,
    buscaUnica,
    setBuscaUnica,
    mostrarCadastro,
    setMostrarCadastro,
    abrirCadastro,
    criando,
    erro,
    searchQuery,
    searching,
    resultados,
    handleSelecionar,
    handleTrocar,
    handleCriar,
    disabled,
    variant,
  } = usePatientQuickRegister(props);

  if (selecionado) {
    return (
      <div>
        <div className="flex items-center gap-3 px-3.5 py-3 bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-200 dark:border-green-800">
          <PacienteAvatar fotoUrl={selecionado.foto_url} name={entityName(selecionado)} size="md" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
              {entityName(selecionado)}
            </p>
            {(selecionado.telefone || selecionado.phone) && (
              <p className="text-xs text-gray-600 dark:text-gray-300">
                {formatTelefone(selecionado.telefone || selecionado.phone)}
              </p>
            )}
            {selecionado.cpf ? (
              <p className="text-xs text-gray-500 dark:text-gray-400">CPF {formatCpf(selecionado.cpf)}</p>
            ) : null}
          </div>
          <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
          <button
            type="button"
            onClick={handleTrocar}
            disabled={disabled}
            className="ml-1 text-xs font-medium text-gray-500 hover:text-red-500 shrink-0"
          >
            Trocar
          </button>
        </div>
      </div>
    );
  }

  if (variant === "agenda") {
    return (
      <div className="space-y-2.5">
        {!mostrarCadastro ? (
          <>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="search"
                value={buscaUnica}
                onChange={(e) => setBuscaUnica(e.target.value)}
                placeholder="Buscar por nome, telefone ou CPF..."
                disabled={disabled}
                className={`${inputClass} pl-9`}
                autoFocus
              />
            </div>
            {searchQuery && searching && (
              <p className="text-xs text-gray-500 dark:text-gray-400">Buscando no cadastro...</p>
            )}
            {searchQuery && !searching && resultados.length > 0 && (
              <div className="border border-gray-200 dark:border-neutral-600 rounded-xl overflow-hidden max-h-44 overflow-y-auto bg-white dark:bg-neutral-800">
                {resultados.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handleSelecionar(p)}
                    disabled={disabled}
                    className="w-full text-left px-3 py-2.5 text-sm border-b last:border-b-0 border-gray-100 dark:border-neutral-700 flex items-center gap-2.5 hover:bg-gray-50 dark:hover:bg-neutral-700/60"
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
                Nenhum paciente encontrado — cadastre um novo abaixo.
              </p>
            )}
            <button
              type="button"
              onClick={abrirCadastro}
              disabled={disabled}
              className="inline-flex items-center gap-1.5 text-sm font-semibold"
              style={{ color: theme.primary }}
            >
              <Plus className="h-4 w-4" />
              Novo paciente
            </button>
          </>
        ) : (
          <div
            className="rounded-xl border p-3 space-y-2 dark:border-opacity-40"
            style={{
              borderColor: cbPrimaryAlpha(28),
              backgroundColor: cbPrimaryAlpha(8),
            }}
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-medium" style={{ color: theme.primary }}>
                Cadastro rápido
              </p>
              <button
                type="button"
                className="text-xs text-gray-500 hover:text-gray-700"
                onClick={() => setMostrarCadastro(false)}
              >
                Voltar à busca
              </button>
            </div>
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
                placeholder="(00) 00000-0000 ou e-mail"
                inputMode="tel"
                maxLength={20}
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
              <p className="text-xs text-gray-500">Verificando duplicados...</p>
            )}
            {searchQuery && !searching && resultados.length > 0 && (
              <div className="border border-gray-200 dark:border-neutral-600 rounded-lg overflow-hidden max-h-36 overflow-y-auto bg-white dark:bg-neutral-800">
                <p className="px-3 py-1.5 text-[11px] font-medium text-gray-500 bg-gray-50 dark:bg-neutral-900/50">
                  Já existem no cadastro — selecione ou continue
                </p>
                {resultados.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handleSelecionar(p)}
                    disabled={disabled}
                    className="w-full text-left px-3 py-2 text-sm border-b last:border-b-0 border-gray-100 dark:border-neutral-700"
                  >
                    <span className="font-medium">{entityName(p)}</span>
                  </button>
                ))}
              </div>
            )}
            {erro && <p className="text-xs text-red-600 dark:text-red-400">{erro}</p>}
            <button
              type="button"
              onClick={() => void handleCriar()}
              disabled={disabled || criando || !nomeNovo.trim()}
              className="w-full sm:w-auto px-4 py-2 text-sm font-medium text-white rounded-lg disabled:opacity-50"
              style={{ backgroundColor: theme.primary }}
            >
              {criando ? "Salvando..." : "Salvar novo paciente"}
            </button>
          </div>
        )}
        {erro && mostrarCadastro === false ? (
          <p className="text-xs text-red-600 dark:text-red-400">{erro}</p>
        ) : null}
      </div>
    );
  }

  return (
    <div>
      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Paciente *</label>
      <div
        className="rounded-lg border p-3 space-y-2 dark:border-opacity-40"
        style={{
          borderColor: cbPrimaryAlpha(28),
          backgroundColor: cbPrimaryAlpha(8),
        }}
      >
        <p className="text-xs" style={{ color: theme.primary }}>
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
            placeholder="(00) 00000-0000 ou +código"
            inputMode="tel"
            maxLength={20}
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
                className="w-full text-left px-3 py-2 text-sm border-b last:border-b-0 border-gray-100 dark:border-neutral-700 flex items-center gap-2.5 hover:opacity-90"
                style={{ backgroundColor: "transparent" }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = theme.primaryLight;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                }}
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
          className="w-full sm:w-auto px-4 py-2 text-sm font-medium text-white rounded-lg disabled:opacity-50"
          style={{ backgroundColor: theme.primary }}
        >
          {criando ? "Salvando..." : "Salvar novo paciente"}
        </button>
      </div>
    </div>
  );
}
