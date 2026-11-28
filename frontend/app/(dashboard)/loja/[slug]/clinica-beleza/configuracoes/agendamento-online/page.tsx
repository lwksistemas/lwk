"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, CalendarCheck, Loader2 } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { TabComunicacao } from "@/components/clinica-beleza/agendamento-online/TabComunicacao";
import { TabGeral } from "@/components/clinica-beleza/agendamento-online/TabGeral";
import { TabPagina } from "@/components/clinica-beleza/agendamento-online/TabPagina";
import { TabProcedimentos } from "@/components/clinica-beleza/agendamento-online/TabProcedimentos";
import { TabProfissionais } from "@/components/clinica-beleza/agendamento-online/TabProfissionais";
import {
  agendamentoOnlineAdminApi,
  mensagemErroAgendamentoOnline,
  type AgendamentoOnlineConfig,
} from "@/lib/clinica-beleza-api/agendamento-online";

const TABS = [
  { id: "geral", label: "Geral" },
  { id: "profissionais", label: "Profissionais" },
  { id: "procedimentos", label: "Procedimentos" },
  { id: "comunicacao", label: "Comunicação" },
  { id: "pagina", label: "Página e Acesso" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function ClinicaBelezaAgendamentoOnlineConfigPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;
  const { primary } = useClinicaBelezaTheme();
  const [tab, setTab] = useState<TabId>("geral");
  const [cfg, setCfg] = useState<AgendamentoOnlineConfig | null>(null);
  const [erro, setErro] = useState("");

  const carregar = useCallback(async () => {
    setErro("");
    try {
      setCfg(await agendamentoOnlineAdminApi.getConfig());
    } catch (err) {
      setErro(mensagemErroAgendamentoOnline(err, "Não foi possível carregar as configurações."));
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Agendamento Online"
        subtitle="Disponibilidade, procedimentos e página pública"
        showOffline={false}
        icon={CalendarCheck}
        backHref={base}
      />
      <ClinicaBelezaPageContent>
        <div className="mx-auto w-full max-w-4xl">
          <Link
            href={base}
            className="mb-3 inline-flex items-center gap-1.5 text-sm font-medium hover:underline"
            style={{ color: primary }}
          >
            <ArrowLeft className="h-4 w-4" /> Voltar para configurações
          </Link>

          <div
            role="tablist"
            aria-label="Seções do agendamento online"
            className="mb-4 flex gap-1 overflow-x-auto rounded-2xl border border-[#f0e4e6] bg-white p-1 [scrollbar-width:none] dark:border-gray-700 dark:bg-gray-800 [&::-webkit-scrollbar]:hidden"
          >
            {TABS.map((t) => {
              const ativo = tab === t.id;
              return (
                <button
                  key={t.id}
                  type="button"
                  role="tab"
                  aria-selected={ativo}
                  onClick={() => setTab(t.id)}
                  className={`shrink-0 whitespace-nowrap rounded-xl px-3.5 py-2 text-sm font-medium transition ${
                    ativo ? "text-white shadow-sm" : "text-[#6b5459] hover:bg-pink-50 dark:text-gray-300"
                  }`}
                  style={ativo ? { backgroundColor: primary } : undefined}
                >
                  {t.label}
                </button>
              );
            })}
          </div>

          {erro ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {erro}{" "}
              <button type="button" className="font-semibold underline" onClick={() => void carregar()}>
                Tentar novamente
              </button>
            </div>
          ) : !cfg ? (
            <div className="flex items-center gap-2 py-10 text-sm text-[#8a6e74]">
              <Loader2 className="h-4 w-4 animate-spin" /> Carregando…
            </div>
          ) : (
            <div role="tabpanel">
              {tab === "geral" && <TabGeral cfg={cfg} primary={primary} onSaved={setCfg} />}
              {tab === "profissionais" && <TabProfissionais primary={primary} />}
              {tab === "procedimentos" && <TabProcedimentos primary={primary} />}
              {tab === "comunicacao" && <TabComunicacao cfg={cfg} primary={primary} onSaved={setCfg} />}
              {tab === "pagina" && <TabPagina cfg={cfg} slug={slug} primary={primary} onSaved={setCfg} />}
            </div>
          )}
        </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
