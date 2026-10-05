"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { DollarSign } from "lucide-react";
import apiClient from "@/lib/api-client";
import {
  ClinicaBelezaPageContent,
  ClinicaBelezaPanel,
} from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { OrcamentoPainel } from "@/components/clinica-beleza/consultas/tab-panels/orcamento-tab/OrcamentoTabPanel";
import { useClinicaPodeVerConsulta } from "@/hooks/clinica-beleza/useClinicaPodeVerConsulta";

type ClienteBusca = { id: number; nome: string; cpf?: string };

export default function CriarOrcamentoPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const { podeVerConsulta, loaded } = useClinicaPodeVerConsulta();
  const [termo, setTermo] = useState("");
  const [clientes, setClientes] = useState<ClienteBusca[]>([]);
  const [buscando, setBuscando] = useState(false);
  const [cliente, setCliente] = useState<ClienteBusca | null>(null);

  useEffect(() => {
    if (loaded && !podeVerConsulta) {
      router.replace(`/loja/${slug}/agenda`);
    }
  }, [loaded, podeVerConsulta, router, slug]);

  useEffect(() => {
    const q = termo.trim();
    if (q.length < 2) {
      setClientes([]);
      return;
    }
    let ativo = true;
    setBuscando(true);
    const timer = window.setTimeout(() => {
      apiClient
        .get<ClienteBusca[]>("/clinica-beleza/orcamentos/", { params: { search: q } })
        .then((res) => {
          if (ativo) setClientes(Array.isArray(res.data) ? res.data : []);
        })
        .catch(() => {
          if (ativo) setClientes([]);
        })
        .finally(() => {
          if (ativo) setBuscando(false);
        });
    }, 250);
    return () => {
      ativo = false;
      window.clearTimeout(timer);
    };
  }, [termo]);

  if (!loaded || !podeVerConsulta) {
    return <div className="text-center py-16 text-gray-500">Redirecionando...</div>;
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Criar orçamento"
        subtitle="Não abre atendimento"
        icon={DollarSign}
        showBack={false}
      />
      <ClinicaBelezaPageContent className="space-y-4">
        <ClinicaBelezaPanel className="p-4 md:p-5">
          <label
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            htmlFor="busca-cliente-orcamento"
          >
            Cliente
          </label>
          {cliente ? (
            <div className="flex items-center justify-between gap-3">
              <p className="text-base text-gray-900 dark:text-white min-w-0 truncate">
                {cliente.nome}
                {cliente.cpf ? <span className="text-gray-500"> · {cliente.cpf}</span> : null}
              </p>
              <button
                type="button"
                className="text-sm font-medium shrink-0"
                style={{ color: "var(--cb-primary, #8B3D52)" }}
                onClick={() => {
                  setCliente(null);
                  setTermo("");
                }}
              >
                Trocar
              </button>
            </div>
          ) : (
            <>
              <input
                id="busca-cliente-orcamento"
                value={termo}
                onChange={(e) => setTermo(e.target.value)}
                placeholder="Nome ou CPF"
                className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              {buscando && <p className="text-xs text-gray-500 mt-2">Buscando...</p>}
              {clientes.length > 0 && (
                <ul className="mt-3 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2">
                  {clientes.map((item) => (
                    <li key={item.id}>
                      <button
                        type="button"
                        className="w-full text-left px-3 py-2.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                        onClick={() => setCliente(item)}
                      >
                        <span className="block font-medium text-gray-900 dark:text-white truncate">
                          {item.nome}
                        </span>
                        {item.cpf ? (
                          <span className="block text-xs text-gray-500 mt-0.5">{item.cpf}</span>
                        ) : null}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </ClinicaBelezaPanel>

        {cliente && <OrcamentoPainel patientId={cliente.id} largo />}
      </ClinicaBelezaPageContent>
    </>
  );
}
