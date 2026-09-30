"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { buildConsultaDetailHref } from "@/components/clinica-beleza/consultas-page/consultas-page-utils";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { formatClinicaDataCurta, formatClinicaHora } from "@/lib/clinica-beleza-datetime";
import { currentDashboardMesAno, parseDashboardMesAno } from "@/components/clinica-beleza/clinica-beleza-dashboard/clinica-beleza-dashboard-utils";

interface ProcedimentoRealizado {
  nome: string;
  paciente: string;
  profissional: string;
  realizado_em: string | null;
  consulta_id: number | null;
}

interface ProcedimentosRealizadosData {
  filter?: { label?: string };
  total: number;
  itens: ProcedimentoRealizado[];
}

function mesAnoFromParams(mes: string | null, ano: string | null): string {
  const atual = currentDashboardMesAno();
  const mesNum = Number(mes);
  const anoNum = Number(ano);
  if (!mes || !ano || !Number.isInteger(mesNum) || !Number.isInteger(anoNum) || mesNum < 1 || mesNum > 12) {
    return atual;
  }
  const candidato = `${anoNum}-${String(mesNum).padStart(2, "0")}`;
  return candidato > atual ? atual : candidato;
}

function formatQuando(value: string | null): string {
  if (!value) return "—";
  const data = new Date(value);
  if (Number.isNaN(data.getTime())) return "—";
  return `${formatClinicaDataCurta(data)} ${formatClinicaHora(data)}`;
}

export function ProcedimentosRealizadosPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = params.slug as string;
  const mesAno = mesAnoFromParams(searchParams.get("mes"), searchParams.get("ano"));
  const mesAnoMax = currentDashboardMesAno();

  const [data, setData] = useState<ProcedimentosRealizadosData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const carregar = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { mes, ano } = parseDashboardMesAno(mesAno);
      const response = await clinicaBelezaFetch(
        `/dashboard/procedimentos-realizados/?mes=${mes}&ano=${ano}`,
        {},
        { slug },
      );
      if (!response.ok) {
        setData(null);
        setError("Não foi possível carregar os procedimentos finalizados.");
        return;
      }
      setData(await response.json());
    } catch {
      setData(null);
      setError("Não foi possível carregar os procedimentos finalizados.");
    } finally {
      setLoading(false);
    }
  }, [mesAno, slug]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const label = data?.filter?.label ?? "Este mês";
  const total = data?.total ?? 0;

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={`Procedimentos realizados — ${label}`}
        subtitle={loading ? "Consultas finalizadas no mês" : `${total} procedimento${total === 1 ? "" : "s"} finalizado${total === 1 ? "" : "s"}`}
        backHref={`/loja/${slug}/dashboard`}
        extraActions={
          <input
            type="month"
            value={mesAno}
            max={mesAnoMax}
            onChange={(e) => {
              if (!e.target.value) return;
              const { mes, ano } = parseDashboardMesAno(e.target.value);
              router.replace(`/loja/${slug}/clinica-beleza/procedimentos-realizados?mes=${mes}&ano=${ano}`);
            }}
            className="px-3 py-1.5 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100"
            aria-label="Mês dos procedimentos"
          />
        }
      />
      <ClinicaBelezaPageContent>
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}
        {loading ? (
          <div className="flex justify-center py-12">
            <div
              className="w-10 h-10 border-4 border-t-transparent rounded-full animate-spin"
              style={{ borderColor: "color-mix(in srgb, var(--cb-primary, #8B3D52) 19%, transparent)", borderTopColor: "transparent" }}
            />
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
            {!data?.itens.length ? (
              <p className="text-center py-12 text-gray-500">Nenhum procedimento finalizado neste mês.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">Data</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">Procedimento</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">Cliente</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase hidden md:table-cell">Profissional</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {data.itens.map((item, index) => {
                      const href = item.consulta_id ? buildConsultaDetailHref(slug, item.consulta_id) : null;
                      return (
                        <tr
                          key={`${item.consulta_id ?? item.nome}-${index}`}
                          className={href ? "cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/40" : undefined}
                          onClick={() => {
                            if (href) router.push(href);
                          }}
                          onKeyDown={(event) => {
                            if (href && (event.key === "Enter" || event.key === " ")) {
                              event.preventDefault();
                              router.push(href);
                            }
                          }}
                          tabIndex={href ? 0 : undefined}
                        >
                          <td className="px-4 py-3 whitespace-nowrap text-gray-600 dark:text-gray-300">{formatQuando(item.realizado_em)}</td>
                          <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{item.nome}</td>
                          <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{item.paciente || "—"}</td>
                          <td className="px-4 py-3 text-gray-700 dark:text-gray-300 hidden md:table-cell">{item.profissional || "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
