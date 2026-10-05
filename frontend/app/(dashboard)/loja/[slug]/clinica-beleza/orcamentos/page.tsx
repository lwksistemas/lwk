"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import apiClient from "@/lib/api-client";
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
    <div className="max-w-3xl mx-auto p-4 md:p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Criar orçamento</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Escolha o cliente e monte o orçamento. Não abre atendimento.
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-3">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="busca-cliente-orcamento">
          Cliente
        </label>
        {cliente ? (
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-gray-900 dark:text-white">
              {cliente.nome}
              {cliente.cpf ? <span className="text-gray-500"> · {cliente.cpf}</span> : null}
            </p>
            <button
              type="button"
              className="text-sm text-[#8B3D52] hover:underline"
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
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            {buscando && <p className="text-xs text-gray-500">Buscando...</p>}
            {clientes.length > 0 && (
              <ul className="border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
                {clientes.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
                      onClick={() => setCliente(item)}
                    >
                      {item.nome}
                      {item.cpf ? <span className="text-gray-500"> · {item.cpf}</span> : null}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>

      {cliente && <OrcamentoPainel patientId={cliente.id} />}
    </div>
  );
}
