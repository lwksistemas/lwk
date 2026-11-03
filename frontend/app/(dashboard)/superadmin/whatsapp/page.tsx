"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import apiClient from "@/lib/api-client";
import { authService } from "@/lib/auth";
import { formatTelefone } from "@/lib/format-br";
import {
  classeStatusWhatsapp,
  dataHoraCurta,
  filtrarClientesWhatsapp,
  formatarDocumentoWhatsapp,
  labelStatusWhatsapp,
  labelTipoWhatsapp,
  slugVisivelWhatsapp,
  tempoConectado,
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
    mensagens_total: number;
    mensagens_24h: number;
    mensagens_7d: number;
    mensagens_falhas: number;
  };
  clientes: WhatsappCliente[];
};

type RelatorioFalhas = {
  loja_id: number;
  loja_nome: string;
  total: number;
  dias: number;
  por_motivo: { motivo: string; qtd: number }[];
  por_numero: { telefone: string; qtd: number }[];
  recentes: { data: string; telefone: string; motivo: string; mensagem: string }[];
};

export default function SuperadminWhatsappPage() {
  const router = useRouter();
  const [painel, setPainel] = useState<Painel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [chaveNova, setChaveNova] = useState("");
  const [falhasLojaId, setFalhasLojaId] = useState<number | null>(null);
  const [falhas, setFalhas] = useState<RelatorioFalhas | null>(null);
  const [falhasLoading, setFalhasLoading] = useState(false);

  const verFalhas = useCallback(async (lojaId: number) => {
    if (falhasLojaId === lojaId) {
      setFalhasLojaId(null);
      setFalhas(null);
      return;
    }
    setFalhasLojaId(lojaId);
    setFalhas(null);
    setFalhasLoading(true);
    try {
      const { data } = await apiClient.get<RelatorioFalhas>(`/superadmin/whatsapp/falhas/${lojaId}/?dias=60`);
      setFalhas(data);
    } catch {
      setFalhas(null);
    } finally {
      setFalhasLoading(false);
    }
  }, [falhasLojaId]);

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
    () => filtrarClientesWhatsapp(painel?.clientes ?? [], ""),
    [painel],
  );

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
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
          <div>
            <a href="/superadmin/dashboard" className="text-sm text-green-100 hover:underline">
              ← Dashboard
            </a>
            <h1 className="text-2xl font-bold mt-1">WhatsApp</h1>
            <p className="text-green-100 text-sm">Lojas e números conectados</p>
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

      <main className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {error && <p className="rounded-md bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200 px-4 py-3">{error}</p>}
        {ok && <p className="rounded-md bg-green-50 dark:bg-green-900/30 text-green-800 dark:text-green-200 px-4 py-3">{ok}</p>}
        {chaveNova && (
          <div className="rounded-md border border-amber-300 bg-amber-50 dark:bg-amber-900/20 p-4">
            <p className="text-sm font-medium text-amber-900 dark:text-amber-100 mb-2">Chave (copie agora)</p>
            <code className="block break-all text-sm bg-white dark:bg-gray-900 p-3 rounded">{chaveNova}</code>
            <p className="text-xs text-amber-800 dark:text-amber-200 mt-2">
              No PHP: header Authorization Bearer com esta chave. Teste em GET https://api.lwksistemas.com.br/api/whatsapp/v1/me/
            </p>
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
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                ["Lojas", painel.resumo.clientes, "text-gray-900 dark:text-gray-100"],
                ["Conectados", painel.resumo.conectados, "text-green-700 dark:text-green-300"],
                ["Aguardando QR", painel.resumo.aguardando_qr, painel.resumo.aguardando_qr > 0 ? "text-amber-700 dark:text-amber-300" : "text-gray-900 dark:text-gray-100"],
                ["Desconectados", painel.resumo.desconectados, painel.resumo.desconectados > 0 ? "text-red-600 dark:text-red-400" : "text-gray-900 dark:text-gray-100"],
              ].map(([label, value, cls]) => (
                <div key={String(label)} className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
                  <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
                  <p className={`text-2xl font-semibold tabular-nums ${cls}`}>{value}</p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                ["Mensagens (total)", painel.resumo.mensagens_total, "text-gray-900 dark:text-gray-100"],
                ["Últimas 24h", painel.resumo.mensagens_24h, "text-green-700 dark:text-green-300"],
                ["Últimos 7 dias", painel.resumo.mensagens_7d, "text-gray-900 dark:text-gray-100"],
                ["Falhas", painel.resumo.mensagens_falhas, painel.resumo.mensagens_falhas > 0 ? "text-red-600 dark:text-red-400" : "text-gray-900 dark:text-gray-100"],
              ].map(([label, value, cls]) => (
                <div key={String(label)} className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
                  <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
                  <p className={`text-2xl font-semibold tabular-nums ${cls}`}>{value}</p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
              {clientes.map((c) => {
                const key = `${c.tipo}-${c.id ?? c.loja_id ?? c.nome}`;
                const doc = formatarDocumentoWhatsapp(c.documento);
                const slug = slugVisivelWhatsapp(c.slug, c.documento);
                return (
                  <article key={key} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700">
                    <header className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
                      <div className="flex items-start justify-between gap-3">
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100 leading-snug">{c.nome}</h2>
                        <span className="shrink-0 text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-200">
                          {labelTipoWhatsapp(c.tipo)}
                        </span>
                      </div>
                      {(doc || slug) && (
                        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                          {doc}
                          {doc && slug ? " · " : ""}
                          {slug ? `/${slug}` : ""}
                        </p>
                      )}
                    </header>
                    <div className="px-4 py-3 space-y-3">
                        {c.numeros.length === 0 ? (
                          <p className="text-sm text-gray-500">Nenhum número conectado.</p>
                        ) : (
                          <ul className="space-y-2">
                            {c.numeros.map((n) => {
                              const fone = formatTelefone(n.telefone) || n.telefone;
                              return (
                              <li key={n.instance_name} className="flex items-center justify-between gap-3 text-sm">
                                <span className="min-w-0 text-gray-800 dark:text-gray-200">
                                  <span className="font-medium">{fone || "Número não identificado"}</span>
                                  {n.profile_name && (
                                    <span className="block text-xs text-gray-500">{n.profile_name}</span>
                                  )}
                                </span>
                                <span className="text-right shrink-0">
                                  <span className={`px-2 py-0.5 rounded-full text-xs ${classeStatusWhatsapp(n.status)}`}>
                                    {labelStatusWhatsapp(n.status)}
                                  </span>
                                  {n.status === "connected" && n.conectado_desde && (
                                    <span className="block text-xs text-gray-400 mt-0.5">
                                      {tempoConectado(n.conectado_desde)}
                                    </span>
                                  )}
                                </span>
                              </li>
                              );
                            })}
                          </ul>
                        )}
                        {c.mensagens && c.loja_id != null && (
                          <div className="grid grid-cols-4 gap-2 rounded-md bg-gray-50 dark:bg-gray-900/40 p-3">
                            <div>
                              <p className="text-[11px] text-gray-500">Enviadas</p>
                              <p className="text-sm font-semibold tabular-nums text-gray-900 dark:text-gray-100">{c.mensagens.enviadas}</p>
                            </div>
                            <div>
                              <p className="text-[11px] text-gray-500">24h</p>
                              <p className="text-sm font-semibold tabular-nums text-gray-900 dark:text-gray-100">{c.mensagens.ultimas_24h}</p>
                            </div>
                            <div>
                              <p className="text-[11px] text-gray-500">7 dias</p>
                              <p className="text-sm font-semibold tabular-nums text-gray-900 dark:text-gray-100">{c.mensagens.ultimos_7d}</p>
                            </div>
                            <div>
                              <p className="text-[11px] text-gray-500">Falhas</p>
                              <p className={`text-sm font-semibold tabular-nums ${c.mensagens.falhas > 0 ? "text-red-600 dark:text-red-400" : "text-gray-900 dark:text-gray-100"}`}>{c.mensagens.falhas}</p>
                            </div>
                            {c.mensagens.ultimo_envio && (
                              <div className="col-span-4">
                                <p className="text-[11px] text-gray-500">
                                  Último envio: {dataHoraCurta(c.mensagens.ultimo_envio)}
                                </p>
                              </div>
                            )}
                          </div>
                        )}
                        {c.loja_id != null && c.mensagens && c.mensagens.falhas > 0 && (
                          <div className="space-y-2">
                            <button
                              type="button"
                              onClick={() => void verFalhas(c.loja_id as number)}
                              className="text-sm px-3 py-1.5 rounded-md border border-red-300 text-red-700 dark:text-red-300 dark:border-red-700"
                            >
                              {falhasLojaId === c.loja_id ? "Ocultar falhas" : `Ver falhas (${c.mensagens.falhas})`}
                            </button>
                            {falhasLojaId === c.loja_id && (
                              <div className="rounded-md border border-gray-200 dark:border-gray-700 p-3 space-y-3">
                                {falhasLoading && <p className="text-xs text-gray-500">Carregando relatório...</p>}
                                {!falhasLoading && falhas && falhas.total === 0 && (
                                  <p className="text-xs text-gray-500">Sem falhas nos últimos {falhas.dias} dias.</p>
                                )}
                                {!falhasLoading && falhas && falhas.total > 0 && (
                                  <>
                                    <p className="text-xs text-gray-600 dark:text-gray-300">
                                      <span className="font-semibold">{falhas.total}</span> falhas nos últimos {falhas.dias} dias
                                    </p>
                                    <div>
                                      <p className="text-[11px] font-medium text-gray-500 mb-1">Por motivo</p>
                                      <ul className="space-y-0.5">
                                        {falhas.por_motivo.map((m) => (
                                          <li key={m.motivo} className="flex justify-between text-xs text-gray-700 dark:text-gray-200">
                                            <span>{m.motivo}</span>
                                            <span className="tabular-nums font-semibold">{m.qtd}</span>
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                    <div>
                                      <p className="text-[11px] font-medium text-gray-500 mb-1">Números com mais falhas</p>
                                      <ul className="space-y-0.5">
                                        {falhas.por_numero.map((n) => (
                                          <li key={n.telefone} className="flex justify-between text-xs font-mono text-gray-700 dark:text-gray-200">
                                            <span>{n.telefone}</span>
                                            <span className="tabular-nums font-semibold">{n.qtd}</span>
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                    {falhas.recentes.length > 0 && (
                                      <div>
                                        <p className="text-[11px] font-medium text-gray-500 mb-1">Falhas recentes</p>
                                        <ul className="space-y-1">
                                          {falhas.recentes.slice(0, 8).map((r, i) => (
                                            <li key={`${r.data}-${i}`} className="text-xs text-gray-600 dark:text-gray-300">
                                              <span className="text-gray-400">{dataHoraCurta(r.data)}</span>{" · "}
                                              <span className="font-mono">{r.telefone}</span>{" — "}
                                              <span>{r.motivo}</span>
                                            </li>
                                          ))}
                                        </ul>
                                      </div>
                                    )}
                                  </>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                        {c.tipo === "parceiro" && c.id != null && (
                          <div className="space-y-2">
                            <p className="text-xs text-gray-500">
                              {c.documento ? `${formatarDocumentoWhatsapp(c.documento)} · ` : ""}
                              até {c.quota_numeros} números (clientes do parceiro)
                            </p>
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
                  </article>
                );
              })}
              {clientes.length === 0 && (
                <p className="text-sm text-gray-500">Nenhuma loja com WhatsApp ativo.</p>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
