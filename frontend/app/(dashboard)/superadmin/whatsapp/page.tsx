"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import apiClient from "@/lib/api-client";
import { authService } from "@/lib/auth";
import {
  classeStatusWhatsapp,
  filtrarClientesWhatsapp,
  labelStatusWhatsapp,
  labelTipoWhatsapp,
  type WhatsappCliente,
} from "@/lib/whatsapp-painel-utils";

type Painel = {
  evolution: { configured: boolean; ok: boolean; error: string | null };
  resumo: {
    clientes: number;
    conectados: number;
    aguardando_qr: number;
    desconectados: number;
    parceiros: number;
  };
  clientes: WhatsappCliente[];
};

export default function SuperadminWhatsappPage() {
  const router = useRouter();
  const [painel, setPainel] = useState<Painel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [filtro, setFiltro] = useState("");
  const [aberto, setAberto] = useState<string | null>(null);
  const [parceiroNome, setParceiroNome] = useState("");
  const [chaveNova, setChaveNova] = useState("");

  const carregar = useCallback(async () => {
    setError("");
    try {
      const { data } = await apiClient.get<Painel>("/superadmin/whatsapp/painel/");
      setPainel(data);
    } catch {
      setError("Não foi possível carregar o painel WhatsApp.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authService.isAuthenticated() || authService.getUserType() !== "superadmin") {
      router.push("/superadmin/login");
      return;
    }
    void carregar();
  }, [carregar, router]);

  const clientes = useMemo(
    () => filtrarClientesWhatsapp(painel?.clientes ?? [], filtro),
    [filtro, painel],
  );

  const criarParceiro = async () => {
    setError("");
    setOk("");
    try {
      await apiClient.post("/superadmin/whatsapp/parceiros/", { nome: parceiroNome });
      setParceiroNome("");
      setOk("Parceiro cadastrado.");
      await carregar();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error;
      setError(msg || "Não foi possível cadastrar o parceiro.");
    }
  };

  const emitirChave = async (customerId: number) => {
    setError("");
    setChaveNova("");
    try {
      const { data } = await apiClient.post<{ chave: string }>(
        `/superadmin/whatsapp/parceiros/${customerId}/chaves/`,
        { nome: "painel" },
      );
      setChaveNova(data.chave);
      setOk("Chave gerada. Copie agora — ela não aparece de novo.");
      await carregar();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error;
      setError(msg || "Não foi possível emitir a chave.");
    }
  };

  const revogarChave = async (customerId: number, keyId: number) => {
    if (!confirm("Revogar esta chave? O sistema PHP para de autenticar.")) return;
    await apiClient.post(`/superadmin/whatsapp/parceiros/${customerId}/chaves/${keyId}/revogar/`);
    setOk("Chave revogada.");
    await carregar();
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-green-800 dark:bg-green-950 text-white shadow">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div>
            <a href="/superadmin/dashboard" className="text-sm text-green-100 hover:underline">
              ← Dashboard
            </a>
            <h1 className="text-2xl font-bold mt-1">WhatsApp</h1>
            <p className="text-green-100 text-sm">Clientes e números conectados (Evolution fica oculta)</p>
          </div>
          <button
            type="button"
            onClick={() => void carregar()}
            className="px-3 py-2 rounded-md bg-white/10 hover:bg-white/20 text-sm"
          >
            Atualizar
          </button>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {error && <p className="rounded-md bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200 px-4 py-3">{error}</p>}
        {ok && <p className="rounded-md bg-green-50 dark:bg-green-900/30 text-green-800 dark:text-green-200 px-4 py-3">{ok}</p>}
        {chaveNova && (
          <div className="rounded-md border border-amber-300 bg-amber-50 dark:bg-amber-900/20 p-4">
            <p className="text-sm font-medium text-amber-900 dark:text-amber-100 mb-2">Chave (copie agora)</p>
            <code className="block break-all text-sm bg-white dark:bg-gray-900 p-3 rounded">{chaveNova}</code>
          </div>
        )}

        {loading || !painel ? (
          <p className="text-gray-500">Carregando...</p>
        ) : (
          <>
            {!painel.evolution.ok && (
              <p className="text-sm text-amber-800 dark:text-amber-200">
                {painel.evolution.error || "Evolution indisponível neste ambiente."}
              </p>
            )}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {[
                ["Clientes", painel.resumo.clientes],
                ["Conectados", painel.resumo.conectados],
                ["Aguardando QR", painel.resumo.aguardando_qr],
                ["Desconectados", painel.resumo.desconectados],
                ["Parceiros", painel.resumo.parceiros],
              ].map(([label, value]) => (
                <div key={String(label)} className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
                  <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
                  <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{value}</p>
                </div>
              ))}
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm flex flex-col md:flex-row gap-3 md:items-end">
              <label className="flex-1 text-sm text-gray-700 dark:text-gray-300">
                Novo parceiro (API PHP)
                <input
                  value={parceiroNome}
                  onChange={(e) => setParceiroNome(e.target.value)}
                  className="mt-1 w-full border rounded-md px-3 py-2 dark:bg-gray-900 dark:border-gray-600"
                  placeholder="Nome do sistema cliente"
                />
              </label>
              <button
                type="button"
                onClick={() => void criarParceiro()}
                disabled={!parceiroNome.trim()}
                className="px-4 py-2 rounded-md bg-green-700 text-white text-sm disabled:opacity-50"
              >
                Cadastrar parceiro
              </button>
            </div>

            <input
              value={filtro}
              onChange={(e) => setFiltro(e.target.value)}
              placeholder="Buscar cliente, loja ou número..."
              className="w-full border rounded-md px-3 py-2 dark:bg-gray-800 dark:border-gray-600"
            />

            <div className="space-y-3">
              {clientes.map((c) => {
                const key = `${c.tipo}-${c.id ?? c.loja_id ?? c.nome}`;
                const abertoAgora = aberto === key;
                return (
                  <article key={key} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700">
                    <button
                      type="button"
                      onClick={() => setAberto(abertoAgora ? null : key)}
                      className="w-full text-left px-4 py-3 flex items-center justify-between gap-3"
                    >
                      <span>
                        <span className="font-semibold text-gray-900 dark:text-gray-100">{c.nome}</span>
                        <span className="ml-2 text-xs text-gray-500">{labelTipoWhatsapp(c.tipo)}</span>
                        {c.slug && <span className="ml-2 text-xs text-gray-400">/{c.slug}</span>}
                      </span>
                      <span className="text-sm text-gray-500">
                        {c.numeros.filter((n) => n.status === "connected").length}/{c.numeros.length || 0} conectado(s)
                      </span>
                    </button>
                    {abertoAgora && (
                      <div className="px-4 pb-4 space-y-3 border-t border-gray-100 dark:border-gray-700 pt-3">
                        {c.numeros.length === 0 ? (
                          <p className="text-sm text-gray-500">Nenhum número nesta Evolution.</p>
                        ) : (
                          <ul className="space-y-2">
                            {c.numeros.map((n) => (
                              <li key={n.instance_name} className="flex items-center justify-between text-sm">
                                <span className="font-mono text-gray-800 dark:text-gray-200">
                                  {n.telefone || n.instance_name}
                                  <span className="block text-xs text-gray-400">{n.instance_name}</span>
                                </span>
                                <span className={`px-2 py-0.5 rounded-full text-xs ${classeStatusWhatsapp(n.status)}`}>
                                  {labelStatusWhatsapp(n.status)}
                                </span>
                              </li>
                            ))}
                          </ul>
                        )}
                        {c.tipo === "parceiro" && c.id != null && (
                          <div className="space-y-2">
                            <button
                              type="button"
                              onClick={() => void emitirChave(c.id as number)}
                              className="text-sm px-3 py-1.5 rounded-md border border-green-700 text-green-800 dark:text-green-200"
                            >
                              Gerar chave API
                            </button>
                            {c.chaves.map((ch) => (
                              <div key={ch.id} className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-300">
                                <span>
                                  {ch.prefixo}… {ch.revogada ? "(revogada)" : ""}
                                </span>
                                {!ch.revogada && (
                                  <button type="button" className="text-red-600" onClick={() => void revogarChave(c.id as number, ch.id)}>
                                    Revogar
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </article>
                );
              })}
              {clientes.length === 0 && (
                <p className="text-sm text-gray-500">Nenhum cliente neste filtro.</p>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
