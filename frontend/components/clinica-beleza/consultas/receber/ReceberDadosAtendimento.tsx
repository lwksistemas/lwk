"use client";

import { formatCurrency } from "@/lib/financeiro-helpers";
import { consultaProcedimentosNomes, type Consulta } from "../consultas-types";

const fieldClass =
  "w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600";

interface ReceberDadosAtendimentoProps {
  consulta: Consulta;
  valorConsulta: number;
  valorProcedimentos: number;
  total: number;
  saldoAtual: number;
  desconto: string;
  onDescontoChange: (value: string) => void;
  totalLiquido: number;
}

export function ReceberDadosAtendimento({
  consulta,
  valorConsulta,
  valorProcedimentos,
  total,
  saldoAtual,
  desconto,
  onDescontoChange,
  totalLiquido,
}: ReceberDadosAtendimentoProps) {
  return (
    <div className="space-y-2 text-sm">
      <p className="text-gray-500 dark:text-gray-400 text-xs uppercase font-semibold">
        Dados do atendimento
      </p>
      <p>
        <strong>Paciente:</strong> {consulta.patient_name}
      </p>
      <p>
        <strong>Procedimento:</strong> {consultaProcedimentosNomes(consulta)}
      </p>
      <p>
        <strong>Valor da consulta:</strong> {formatCurrency(valorConsulta)}
      </p>
      <p>
        <strong>Valor procedimento:</strong> {formatCurrency(valorProcedimentos)}
      </p>
      <p className="font-semibold text-gray-800 dark:text-gray-200 pt-1 border-t dark:border-neutral-600">
        Total: {formatCurrency(total)}
      </p>
      {Number(consulta.valor_pago ?? 0) > 0 && (
        <p className="text-orange-600 dark:text-orange-400 font-medium">
          Já pago: {formatCurrency(Number(consulta.valor_pago))} · Saldo:{" "}
          {formatCurrency(saldoAtual)}
        </p>
      )}
      {Number(consulta.valor_pago ?? 0) > 0 && saldoAtual > 0 && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Complemente o saldo com uma ou mais formas (Dinheiro, PIX, Débito, Crédito…).
        </p>
      )}
      <div className="pt-3">
        <label className="block text-sm font-medium mb-1">Desconto (R$)</label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={desconto}
          onChange={(e) => onDescontoChange(e.target.value)}
          className={fieldClass}
          placeholder="0,00"
        />
      </div>
      <p className="text-base font-bold text-[#8B4557] dark:text-rose-300 pt-1">
        Total a receber: {formatCurrency(totalLiquido)}
      </p>
    </div>
  );
}
