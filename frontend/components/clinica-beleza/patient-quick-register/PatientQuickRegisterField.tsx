"use client";

import { CheckCircle2, Plus, Search, X } from "lucide-react";
import { formatCpf, formatTelefone } from "@/lib/format-br";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { entityName } from "@/lib/clinica-beleza-entities";
import { cbPrimaryAlpha } from "@/lib/clinica-beleza-theme-utils";
import type { PatientQuickRegisterFieldProps } from "./patient-quick-register-types";
import { usePatientQuickRegister } from "./usePatientQuickRegister";

const inputClass =
  "w-full px-2 py-1 text-sm border border-[#E9D5E3] dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 min-h-[32px]";

function metaPaciente(p: { telefone?: string | null; phone?: string | null; cpf?: string | null }) {
  const tel = p.telefone || p.phone ? formatTelefone(p.telefone || p.phone) : "";
  const cpf = p.cpf ? `CPF ${formatCpf(p.cpf)}` : "";
  if (tel && cpf) return `${tel} · ${cpf}`;
  return tel || cpf;
}

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

  if (selecionado && variant === "agenda") {
    return (
      <div className="space-y-1.5">
        <div
          className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-xl border bg-white dark:bg-neutral-800 min-h-[48px]"
          style={{
            borderColor: cbPrimaryAlpha(22),
            backgroundColor: cbPrimaryAlpha(6),
          }}
        >
          <PacienteAvatar fotoUrl={selecionado.foto_url} name={entityName(selecionado)} size="sm" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate leading-tight">
              {entityName(selecionado)}
            </p>
            {metaPaciente(selecionado) ? (
              <p className="text-xs text-slate-500 dark:text-gray-400 truncate mt-0.5">
                {metaPaciente(selecionado)}
              </p>
            ) : null}
          </div>
          <CheckCircle2 className="h-5 w-5 text-[#22C55E] shrink-0" />
          <button
            type="button"
            onClick={handleTrocar}
            disabled={disabled}
            className="text-xs font-semibold text-slate-500 hover:text-slate-700 dark:hover:text-gray-200 shrink-0 px-1"
          >
            Trocar
          </button>
        </div>
        <div className="flex justify-center">
          <button
            type="button"
            onClick={() => {
              handleTrocar();
              abrirCadastro();
            }}
            disabled={disabled}
            className="inline-flex items-center gap-1 text-[12px] font-semibold"
            style={{ color: theme.primary }}
          >
            <Plus className="h-3.5 w-3.5" />
            Novo paciente
          </button>
        </div>
      </div>
    );
  }

  if (selecionado) {
    return (
      <div>
        <div
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl border bg-white dark:bg-neutral-800"
          style={{
            borderColor: cbPrimaryAlpha(22),
            backgroundColor: cbPrimaryAlpha(6),
          }}
        >
          <PacienteAvatar fotoUrl={selecionado.foto_url} name={entityName(selecionado)} size="md" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
              {entityName(selecionado)}
            </p>
            {metaPaciente(selecionado) ? (
              <p className="text-xs text-slate-500 dark:text-gray-400 truncate">{metaPaciente(selecionado)}</p>
            ) : null}
          </div>
          <CheckCircle2 className="h-5 w-5 text-[#22C55E] shrink-0" />
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
      <div className="space-y-2">
        {!mostrarCadastro ? (
          <>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
              <input
                type="search"
                value={buscaUnica}
                onChange={(e) => setBuscaUnica(e.target.value)}
                placeholder="Buscar por nome, telefone ou CPF..."
                disabled={disabled}
                className={`${inputClass} pl-8 pr-9`}
                autoFocus
              />
              {buscaUnica ? (
                <button
                  type="button"
                  onClick={() => setBuscaUnica("")}
                  disabled={disabled}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded text-gray-400 hover:text-gray-600"
                  aria-label="Limpar busca"
                >
                  <X className="h-4 w-4" />
                </button>
              ) : null}
            </div>
            {searchQuery && searching ? (
              <p className="text-xs text-gray-500 dark:text-gray-400">Buscando no cadastro...</p>
            ) : null}
            {searchQuery && !searching && resultados.length > 0 ? (
              <div className="border border-[#E9D5E3] dark:border-neutral-600 rounded-xl overflow-hidden max-h-40 overflow-y-auto bg-white dark:bg-neutral-800">
                {resultados.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handleSelecionar(p)}
                    disabled={disabled}
                    className="w-full text-left px-2.5 py-2 text-sm border-b last:border-b-0 border-gray-100 dark:border-neutral-700 flex items-center gap-2 hover:bg-gray-50 dark:hover:bg-neutral-700/60"
                  >
                    <PacienteAvatar fotoUrl={p.foto_url} name={entityName(p)} size="sm" />
                    <span className="min-w-0 flex-1">
                      <span className="font-medium block truncate">{entityName(p)}</span>
                      <span className="text-[11px] text-slate-500">{metaPaciente(p)}</span>
                    </span>
                  </button>
                ))}
              </div>
            ) : null}
            {searchQuery && !searching && resultados.length === 0 ? (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Nenhum paciente encontrado — cadastre um novo abaixo.
              </p>
            ) : null}
            <div className="flex justify-center pt-0.5">
              <button
                type="button"
                onClick={abrirCadastro}
                disabled={disabled}
                className="inline-flex items-center gap-1 text-[13px] font-semibold"
                style={{ color: theme.primary }}
              >
                <Plus className="h-3.5 w-3.5" />
                Novo paciente
              </button>
            </div>
          </>
        ) : (
          <div
            className="rounded-xl border p-2.5 space-y-2 dark:border-opacity-40"
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
            {searchQuery && searching ? (
              <p className="text-xs text-gray-500">Verificando duplicados...</p>
            ) : null}
            {searchQuery && !searching && resultados.length > 0 ? (
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
            ) : null}
            {erro ? <p className="text-xs text-red-600 dark:text-red-400">{erro}</p> : null}
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
        {erro && !mostrarCadastro ? (
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

        {searchQuery && searching ? (
          <p className="text-xs text-gray-500 dark:text-gray-400">Buscando no cadastro...</p>
        ) : null}

        {searchQuery && !searching && resultados.length > 0 ? (
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
                  <span className="text-xs text-gray-500">{metaPaciente(p)}</span>
                </span>
              </button>
            ))}
          </div>
        ) : null}

        {searchQuery && !searching && resultados.length === 0 ? (
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Nenhum paciente no cadastro — preencha e salve como novo.
          </p>
        ) : null}

        {erro ? <p className="text-xs text-red-600 dark:text-red-400">{erro}</p> : null}

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
