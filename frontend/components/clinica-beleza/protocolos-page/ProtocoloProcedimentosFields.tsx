"use client";

import { useMemo, useState } from "react";
import { entityName, procedurePrice } from "@/lib/clinica-beleza-entities";
import { procedureCategoriaLabel, resolveProcedureCategoriaSlug } from "@/lib/clinica-beleza-categories";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { precoDaPromocao } from "./protocolos-page-utils";
import {
  FORM_INPUT_CLASS,
  FORM_LABEL_CLASS,
  FORM_SECTION_TITLE_CLASS,
  type ProtocoloFormState,
  type ProtocoloProcedureOption,
} from "./protocolos-page-types";

interface ProtocoloProcedimentosFieldsProps {
  form: ProtocoloFormState;
  procedures: ProtocoloProcedureOption[];
  onChange: (patch: Partial<ProtocoloFormState>) => void;
}

export function ProtocoloProcedimentosFields({ form, procedures, onChange }: ProtocoloProcedimentosFieldsProps) {
  const [categoria, setCategoria] = useState("");
  const [procedureId, setProcedureId] = useState("");
  const [erro, setErro] = useState("");

  const candidatos = useMemo(
    () => procedures.filter((item) => resolveProcedureCategoriaSlug(item.categoria) !== "protocolo"),
    [procedures],
  );
  const categorias = useMemo(() => {
    const mapa = new Map<string, string>();
    for (const item of candidatos) {
      const slug = resolveProcedureCategoriaSlug(item.categoria) || "outro";
      if (!mapa.has(slug)) mapa.set(slug, procedureCategoriaLabel(item.categoria) || slug);
    }
    return [...mapa.entries()]
      .map(([slug, nome]) => ({ slug, nome }))
      .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  }, [candidatos]);
  const daCategoria = candidatos.filter(
    (item) =>
      resolveProcedureCategoriaSlug(item.categoria) === categoria
      && !form.procedimentos.some((linha) => linha.procedure === String(item.id)),
  );

  const conta = precoDaPromocao(
    form.procedimentos.map((linha) => ({
      preco: Number(linha.preco) || 0,
      desconto_tipo: linha.desconto_tipo,
      desconto_valor: Number(String(linha.desconto_valor).replace(",", ".")) || 0,
    })),
    form.desconto_escopo,
    form.desconto_tipo,
    Number(String(form.desconto_valor).replace(",", ".")) || 0,
  );

  const incluir = () => {
    const item = daCategoria.find((procedimento) => String(procedimento.id) === procedureId);
    if (!item) {
      setErro("Escolha o procedimento.");
      return;
    }
    setErro("");
    onChange({
      procedimentos: [
        ...form.procedimentos,
        {
          procedure: String(item.id),
          nome: entityName(item),
          preco: procedurePrice(item) || "0",
          desconto_tipo: "percentual",
          desconto_valor: "0",
        },
      ],
    });
    setProcedureId("");
  };

  return (
    <div className="space-y-4">
      <p className={FORM_SECTION_TITLE_CLASS}>Procedimentos da promoção</p>
      <p className="text-xs text-gray-500">
        Inclua os procedimentos já cadastrados, como Botox e Tirzepatida. O valor cobrado é a soma deles, com o desconto abaixo. Na agenda, o mesmo desconto incide sobre o preço do convênio da cliente.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,11rem)_minmax(0,1fr)_auto] gap-2">
        <select
          value={categoria}
          onChange={(e) => {
            setCategoria(e.target.value);
            setProcedureId("");
            setErro("");
          }}
          className={FORM_INPUT_CLASS}
          aria-label="Categoria do procedimento"
        >
          <option value="">Categoria</option>
          {categorias.map((item) => (
            <option key={item.slug} value={item.slug}>{item.nome}</option>
          ))}
        </select>
        <select
          value={procedureId}
          onChange={(e) => {
            setProcedureId(e.target.value);
            setErro("");
          }}
          disabled={!categoria}
          className={FORM_INPUT_CLASS}
          aria-label="Procedimento da promoção"
        >
          <option value="">{categoria ? "Procedimento" : "Escolha a categoria"}</option>
          {daCategoria.map((item) => (
            <option key={item.id} value={item.id}>
              {entityName(item)} — {formatCurrency(procedurePrice(item))}
            </option>
          ))}
        </select>
        <button type="button" onClick={incluir} className="px-3 py-2 text-sm rounded-lg border shrink-0">
          Incluir
        </button>
      </div>
      {erro ? <p className="text-sm text-red-600">{erro}</p> : null}

      {form.procedimentos.length > 0 ? (
        <div className="space-y-2">
          <label className="text-sm block">
            Desconto
            <select
              value={form.desconto_escopo}
              onChange={(e) => onChange({ desconto_escopo: e.target.value as ProtocoloFormState["desconto_escopo"] })}
              className={`${FORM_INPUT_CLASS} mt-1 max-w-sm`}
            >
              <option value="total">No total dos procedimentos</option>
              <option value="individual">Em cada procedimento</option>
            </select>
          </label>
          {form.procedimentos.map((linha) => (
            <div key={linha.procedure} className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_9rem_7rem_auto] gap-2 items-center">
              <span className="text-sm min-w-0 break-words">
                {linha.nome}
                <span className="text-gray-500"> · {formatCurrency(linha.preco)}</span>
              </span>
              {form.desconto_escopo === "individual" ? (
                <>
                  <select
                    value={linha.desconto_tipo}
                    aria-label={`Tipo de desconto de ${linha.nome}`}
                    onChange={(e) =>
                      onChange({
                        procedimentos: form.procedimentos.map((atual) =>
                          atual.procedure === linha.procedure
                            ? { ...atual, desconto_tipo: e.target.value as "percentual" | "fixo" }
                            : atual,
                        ),
                      })
                    }
                    className={FORM_INPUT_CLASS}
                  >
                    <option value="percentual">Porcentagem</option>
                    <option value="fixo">Valor fixo (R$)</option>
                  </select>
                  <input
                    value={linha.desconto_valor}
                    aria-label={`Desconto de ${linha.nome}`}
                    onChange={(e) =>
                      onChange({
                        procedimentos: form.procedimentos.map((atual) =>
                          atual.procedure === linha.procedure
                            ? { ...atual, desconto_valor: e.target.value }
                            : atual,
                        ),
                      })
                    }
                    className={FORM_INPUT_CLASS}
                    inputMode="decimal"
                  />
                </>
              ) : (
                <span className="hidden sm:block" />
              )}
              <button
                type="button"
                className="text-sm text-red-600"
                onClick={() =>
                  onChange({
                    procedimentos: form.procedimentos.filter((atual) => atual.procedure !== linha.procedure),
                  })
                }
              >
                Remover
              </button>
            </div>
          ))}
          {form.desconto_escopo === "total" ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-md">
              <label className={FORM_LABEL_CLASS}>
                Tipo
                <select
                  value={form.desconto_tipo}
                  onChange={(e) => onChange({ desconto_tipo: e.target.value as ProtocoloFormState["desconto_tipo"] })}
                  className={`${FORM_INPUT_CLASS} mt-1`}
                >
                  <option value="percentual">Porcentagem</option>
                  <option value="fixo">Valor fixo (R$)</option>
                </select>
              </label>
              <label className={FORM_LABEL_CLASS}>
                {form.desconto_tipo === "percentual" ? "Porcentagem" : "Valor (R$)"}
                <input
                  value={form.desconto_valor}
                  onChange={(e) => onChange({ desconto_valor: e.target.value })}
                  className={`${FORM_INPUT_CLASS} mt-1`}
                  inputMode="decimal"
                />
              </label>
            </div>
          ) : null}
          <div className="text-sm rounded-lg border border-gray-200 dark:border-neutral-700 px-3 py-2 max-w-sm">
            <p>Soma {formatCurrency(conta.bruto)}</p>
            <p>Desconto {formatCurrency(conta.desconto)}</p>
            <p className="font-semibold">Total {formatCurrency(conta.liquido)}</p>
          </div>
        </div>
      ) : (
        <p className="text-sm text-gray-500">Nenhum procedimento incluído. Sem esta lista, o pacote continua usando o preço do procedimento da categoria Protocolo.</p>
      )}
    </div>
  );
}
