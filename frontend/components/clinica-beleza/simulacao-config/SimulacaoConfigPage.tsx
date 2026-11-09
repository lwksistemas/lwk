"use client";

import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { simulacaoEsteticaApi, type SimulacaoEsteticaConfig } from "@/lib/clinica-beleza-api/client-ops";

function mensagemErro(err: unknown): string {
  if (err && typeof err === "object" && "error" in err) {
    const texto = (err as { error?: unknown }).error;
    if (typeof texto === "string" && texto.trim()) return texto;
  }
  return "Não foi possível salvar a configuração.";
}

export function SimulacaoConfigPage({ voltarHref }: { voltarHref: string }) {
  const [config, setConfig] = useState<SimulacaoEsteticaConfig | null>(null);
  const [chave, setChave] = useState("");
  const [ativa, setAtiva] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");

  useEffect(() => {
    let vivo = true;
    simulacaoEsteticaApi
      .config()
      .then((dados) => {
        if (!vivo) return;
        setConfig(dados);
        setAtiva(dados.ativa);
      })
      .catch((err) => {
        if (vivo) setErro(mensagemErro(err));
      })
      .finally(() => {
        if (vivo) setLoading(false);
      });
    return () => {
      vivo = false;
    };
  }, []);

  async function salvar() {
    setSaving(true);
    setErro("");
    setAviso("");
    try {
      const dados = await simulacaoEsteticaApi.salvar({
        ativa,
        ...(chave.trim() ? { api_key: chave.trim() } : {}),
      });
      setConfig(dados);
      setAtiva(dados.ativa);
      setChave("");
      setAviso("Configuração salva nesta clínica.");
    } catch (err) {
      setErro(mensagemErro(err));
    } finally {
      setSaving(false);
    }
  }

  async function removerChave() {
    setSaving(true);
    setErro("");
    setAviso("");
    try {
      const dados = await simulacaoEsteticaApi.salvar({ limpar_chave: true });
      setConfig(dados);
      setAtiva(false);
      setChave("");
      setAviso("Chave removida desta clínica.");
    } catch (err) {
      setErro(mensagemErro(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Simulação estética"
        subtitle="Chave YouCam API desta clínica"
        showOffline={false}
        icon={Sparkles}
        backHref={voltarHref}
      />
      <ClinicaBelezaPageContent className="max-w-2xl space-y-4">
        {loading ? (
          <p className="text-sm text-gray-500">Carregando…</p>
        ) : config && !config.disponivel ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100">
            {config.mensagem || "Simulação estética disponível apenas no plano Completo."}
          </div>
        ) : config ? (
          <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4 dark:border-gray-700 dark:bg-gray-800">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Cada clínica usa a própria conta YouCam. A chave fica criptografada e vale só para esta loja.
              Crie a conta em yce.perfectcorp.com, copie a chave da API e cole abaixo. O plano Completo é o
              único que libera esta configuração.
            </p>
            <p className="text-sm text-gray-700 dark:text-gray-200">
              Chave nesta clínica:{" "}
              <strong>{config?.chave_configurada ? "configurada" : "ainda não configurada"}</strong>
            </p>
            <label className="block text-sm font-medium text-gray-800 dark:text-gray-100">
              Chave da API
              <input
                type="password"
                autoComplete="off"
                value={chave}
                onChange={(event) => setChave(event.target.value)}
                placeholder={config?.chave_configurada ? "Cole uma nova chave para substituir" : "Cole a chave da YouCam"}
                className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-900"
              />
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-100">
              <input
                type="checkbox"
                checked={ativa}
                onChange={(event) => setAtiva(event.target.checked)}
              />
              Ativar simulação nesta clínica
            </label>
            {erro && <p className="text-sm text-red-600">{erro}</p>}
            {aviso && <p className="text-sm text-green-700 dark:text-green-400">{aviso}</p>}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void salvar()}
                disabled={saving}
                className="rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
                style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
              >
                {saving ? "Salvando…" : "Salvar"}
              </button>
              {config?.chave_configurada && (
                <button
                  type="button"
                  onClick={() => void removerChave()}
                  disabled={saving}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 dark:border-gray-600 dark:text-gray-200"
                >
                  Remover chave
                </button>
              )}
            </div>
          </div>
        ) : (
          erro && <p className="text-sm text-red-600">{erro}</p>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
