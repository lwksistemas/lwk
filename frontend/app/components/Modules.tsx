"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Check, X } from "lucide-react";
import { IconRenderer } from "@/components/shared/IconRenderer";
import { SectionContainer } from "@/components/shared/SectionContainer";
import { DEFAULT_MODULOS } from "@/lib/homepage-constants";
import type { Modulo } from "@/types/homepage";

interface ModulesProps {
  modulos: Modulo[];
}

interface BeneficioPlano {
  label: string;
  detalhe: string;
  incluso: boolean;
}

interface PlanoValor {
  nome: string;
  resumo: string;
  precoMensal: string;
  precoAnual: string;
  storage: string;
  beneficios: BeneficioPlano[];
  destaque?: boolean;
}

const PLANOS_CLINICA_BELEZA: PlanoValor[] = [
  {
    nome: "Básico",
    resumo:
      "Para começar o atendimento: agenda, cadastro de pacientes e prontuário digital. Sem fotos no servidor, WhatsApp, NFSe nem Memed.",
    precoMensal: "R$ 99,90",
    precoAnual: "R$ 999",
    storage: "1 GB",
    beneficios: [
      {
        label: "Agenda, pacientes e prontuário",
        detalhe: "Consultas, fichas e evolução clínica no dia a dia.",
        incluso: true,
      },
      {
        label: "Fotos de acompanhamento",
        detalhe: "Upload e QR para fotos antes/depois na consulta.",
        incluso: false,
      },
      {
        label: "WhatsApp",
        detalhe: "Confirmações e mensagens automáticas da agenda.",
        incluso: false,
      },
      {
        label: "NFSe e relatórios avançados",
        detalhe: "Nota fiscal de serviço e painéis de gestão.",
        incluso: false,
      },
      {
        label: "Memed (prescrição digital)",
        detalhe: "Prescrição eletrônica integrada à consulta.",
        incluso: false,
      },
    ],
  },
  {
    nome: "Intermediário",
    resumo:
      "Tudo do Básico, mais fotos de acompanhamento no servidor de mídia (painel e QR). Ideal para clínicas que registram evolução visual.",
    precoMensal: "R$ 149,90",
    precoAnual: "R$ 1.499",
    storage: "10 GB",
    beneficios: [
      {
        label: "Agenda, pacientes e prontuário",
        detalhe: "Consultas, fichas e evolução clínica no dia a dia.",
        incluso: true,
      },
      {
        label: "Fotos de acompanhamento",
        detalhe: "Upload e QR para fotos antes/depois na consulta.",
        incluso: true,
      },
      {
        label: "WhatsApp",
        detalhe: "Confirmações e mensagens automáticas da agenda.",
        incluso: false,
      },
      {
        label: "NFSe e relatórios avançados",
        detalhe: "Nota fiscal de serviço e painéis de gestão.",
        incluso: false,
      },
      {
        label: "Memed (prescrição digital)",
        detalhe: "Prescrição eletrônica integrada à consulta.",
        incluso: false,
      },
    ],
  },
  {
    nome: "Completo",
    resumo:
      "Pacote full: fotos, WhatsApp, NFSe, relatórios e Memed. Para clínicas que querem operação, comunicação e prescrição no mesmo sistema.",
    precoMensal: "R$ 199,90",
    precoAnual: "R$ 1.999",
    storage: "25 GB",
    destaque: true,
    beneficios: [
      {
        label: "Agenda, pacientes e prontuário",
        detalhe: "Consultas, fichas e evolução clínica no dia a dia.",
        incluso: true,
      },
      {
        label: "Fotos de acompanhamento",
        detalhe: "Upload e QR para fotos antes/depois na consulta.",
        incluso: true,
      },
      {
        label: "WhatsApp",
        detalhe: "Confirmações e mensagens automáticas da agenda.",
        incluso: true,
      },
      {
        label: "NFSe e relatórios avançados",
        detalhe: "Nota fiscal de serviço e painéis de gestão.",
        incluso: true,
      },
      {
        label: "Memed (prescrição digital)",
        detalhe: "Prescrição eletrônica integrada à consulta.",
        incluso: true,
      },
    ],
  },
];

function isClinicaBeleza(m: Modulo): boolean {
  const slug = (m.slug || "").toLowerCase();
  const nome = (m.nome || "").toLowerCase();
  return (
    slug.includes("clinica-beleza") ||
    slug.includes("clinica_beleza") ||
    (nome.includes("clinica") && nome.includes("beleza")) ||
    (nome.includes("clínica") && nome.includes("beleza"))
  );
}

export default function Modules({ modulos }: ModulesProps) {
  const items = useMemo(
    () => (modulos?.length ? modulos : DEFAULT_MODULOS.map((m, i) => ({ ...m, id: i }))),
    [modulos]
  );

  const clinica = useMemo(() => items.find(isClinicaBeleza) ?? null, [items]);
  const [selectedId, setSelectedId] = useState<number | string | null>(
    clinica?.id ?? null
  );

  const selected = items.find((m) => m.id === selectedId) ?? null;
  const showClinicaPlanos = selected ? isClinicaBeleza(selected) : false;

  return (
    <SectionContainer id="modulos" background="gray">
      <h2 className="text-2xl sm:text-3xl font-bold text-center mb-3 text-gray-900 dark:text-white">
        Módulos Valores
      </h2>
      <p className="text-center text-gray-600 dark:text-gray-300 mb-8 sm:mb-10 max-w-2xl mx-auto text-sm sm:text-base">
        Escolha o módulo para ver planos, valores e o que muda em cada um.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-8">
        {items.map((m, idx) => {
          const active = selected?.id === m.id;
          return (
            <button
              key={m.id ?? idx}
              type="button"
              onClick={() => setSelectedId(m.id)}
              className={`text-left border-2 p-5 sm:p-6 rounded-xl transition-all h-full bg-gradient-to-br from-white to-blue-50 dark:from-gray-900 dark:to-gray-800 ${
                active
                  ? "border-blue-600 shadow-xl ring-2 ring-blue-200"
                  : "border-gray-200 hover:border-blue-400 hover:shadow-lg"
              }`}
            >
              <IconRenderer icone={m.icone} imagem={m.imagem} alt={m.nome} size="md" />
              <h3 className="text-lg sm:text-xl font-bold mb-2 text-gray-900 dark:text-white">
                {m.nome}
              </h3>
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300">{m.descricao}</p>
              <span className="inline-block mt-4 text-blue-600 font-medium text-sm">
                {active ? "Valores abaixo ↓" : "Ver valores →"}
              </span>
            </button>
          );
        })}
      </div>

      {selected && showClinicaPlanos && (
        <div className="rounded-2xl border border-blue-100 bg-white dark:bg-gray-900 dark:border-gray-700 p-5 sm:p-8 shadow-sm">
          <div className="text-center mb-6">
            <h3 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
              Planos — {selected.nome}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 max-w-3xl mx-auto">
              A diferença entre os planos está nos recursos extras: o Básico cobre a operação
              clínica; o Intermediário libera fotos de acompanhamento; o Completo soma WhatsApp,
              NFSe, relatórios e Memed.
            </p>
          </div>

          <div className="overflow-x-auto mb-8 -mx-1 px-1">
            <table className="w-full min-w-[640px] text-sm border-collapse">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th className="py-3 pr-4 font-semibold text-gray-700 dark:text-gray-200">Recurso</th>
                  <th className="py-3 px-2 font-semibold text-center text-gray-700 dark:text-gray-200">Básico</th>
                  <th className="py-3 px-2 font-semibold text-center text-gray-700 dark:text-gray-200">Intermediário</th>
                  <th className="py-3 pl-2 font-semibold text-center text-blue-700 dark:text-blue-300">Completo</th>
                </tr>
              </thead>
              <tbody className="text-gray-700 dark:text-gray-300">
                {[
                  ["Agenda, pacientes e prontuário", true, true, true],
                  ["Fotos de acompanhamento (mídia + QR)", false, true, true],
                  ["WhatsApp (agenda e mensagens)", false, false, true],
                  ["NFSe e relatórios avançados", false, false, true],
                  ["Memed (prescrição digital)", false, false, true],
                  ["Armazenamento", "1 GB", "10 GB", "25 GB"],
                ].map(([recurso, b, i, c]) => (
                  <tr key={String(recurso)} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="py-2.5 pr-4">{recurso}</td>
                    {[b, i, c].map((val, idx) => (
                      <td key={idx} className="py-2.5 px-2 text-center">
                        {typeof val === "boolean" ? (
                          val ? (
                            <Check className="w-4 h-4 text-green-600 inline-block" />
                          ) : (
                            <X className="w-4 h-4 text-gray-300 inline-block" />
                          )
                        ) : (
                          <span className="font-medium">{val}</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
            {PLANOS_CLINICA_BELEZA.map((plano) => (
              <div
                key={plano.nome}
                className={`rounded-xl border p-5 flex flex-col ${
                  plano.destaque
                    ? "border-blue-600 bg-blue-50/60 dark:bg-blue-950/30 shadow-md"
                    : "border-gray-200 dark:border-gray-700"
                }`}
              >
                {plano.destaque && (
                  <span className="self-start mb-2 text-xs font-semibold uppercase tracking-wide text-blue-700 bg-blue-100 px-2 py-0.5 rounded">
                    Mais completo
                  </span>
                )}
                <h4 className="text-lg font-bold text-gray-900 dark:text-white">{plano.nome}</h4>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                  {plano.resumo}
                </p>
                <p className="mt-3 text-2xl font-bold text-blue-600">{plano.precoMensal}</p>
                <p className="text-sm text-gray-500">por mês</p>
                <p className="text-xs text-gray-500 mt-1">
                  ou {plano.precoAnual}/ano · {plano.storage} de armazenamento
                </p>
                <ul className="mt-4 space-y-3 text-sm flex-1">
                  {plano.beneficios.map((b) => (
                    <li key={b.label} className="flex items-start gap-2">
                      {b.incluso ? (
                        <Check className="w-4 h-4 mt-0.5 text-green-600 shrink-0" />
                      ) : (
                        <X className="w-4 h-4 mt-0.5 text-gray-400 shrink-0" />
                      )}
                      <span className={b.incluso ? "text-gray-800 dark:text-gray-100" : "text-gray-400"}>
                        <span className="font-medium block">{b.label}</span>
                        <span className={`text-xs block mt-0.5 ${b.incluso ? "text-gray-500 dark:text-gray-400" : "text-gray-400"}`}>
                          {b.detalhe}
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>
                <Link
                  href="/cadastro"
                  className={`mt-5 text-center rounded-lg px-4 py-2.5 font-medium transition-colors ${
                    plano.destaque
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-white border border-blue-600 text-blue-600 hover:bg-blue-50"
                  }`}
                >
                  Começar
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {selected && !showClinicaPlanos && (
        <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6 text-center">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
            {selected.nome}
          </h3>
          <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
            Valores e planos disponíveis no cadastro. Fale conosco ou inicie seu teste.
          </p>
          <Link
            href="/cadastro"
            className="inline-block bg-blue-600 text-white px-6 py-2.5 rounded-lg hover:bg-blue-700 font-medium"
          >
            Ver no cadastro
          </Link>
        </div>
      )}
    </SectionContainer>
  );
}
