"use client";

/**
 * Cadastro de Profissionais - Clínica da Beleza
 */

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Plus, Pencil, Trash2, X } from "lucide-react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { OfflineIndicator } from "@/components/clinica-beleza/OfflineIndicator";
import { buscarProfissionaisOffline, salvarProfissionaisOffline, adicionarNaFilaSync, getLojaSlug } from "@/lib/offline-db";

type PerfilAcesso = "administrador" | "profissional" | "recepcao";

interface Professional {
  id: number;
  name: string;
  specialty: string;
  phone: string | null;
  email: string | null;
  active: boolean;
  is_administrador_vinculado?: boolean;
}

interface LojaOwnerInfo {
  owner_username: string;
  owner_email: string;
  owner_telefone: string;
}

export default function ProfissionaisPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const [list, setList] = useState<Professional[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Professional | null>(null);
  const [form, setForm] = useState({
    name: "",
    specialty: "",
    phone: "",
    email: "",
    criar_acesso: false,
    perfil: "profissional" as PerfilAcesso,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [lojaOwnerInfo, setLojaOwnerInfo] = useState<LojaOwnerInfo | null>(null);
  useClinicaBelezaDark();

  const loadLojaInfo = async () => {
    if (!navigator.onLine) return;
    try {
      const res = await clinicaBelezaFetch("/loja-info/");
      if (res.ok) {
        const data = await res.json();
        setLojaOwnerInfo({
          owner_username: data.owner_username ?? "",
          owner_email: data.owner_email ?? "",
          owner_telefone: data.owner_telefone ?? "",
        });
      }
    } catch {
      setLojaOwnerInfo(null);
    }
  };

  const load = async () => {
    setLoading(true);
    try {
      if (!navigator.onLine) {
        const data = await buscarProfissionaisOffline();
        setList(Array.isArray(data) ? (data as Professional[]) : []);
      } else {
        const res = await clinicaBelezaFetch("/professionals/");
        const data = await res.json();
        if (res.ok) {
          const arr = Array.isArray(data) ? data : [];
          setList(arr);
          await salvarProfissionaisOffline(arr);
        } else setList([]);
      }
    } catch {
      setList([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    loadLojaInfo();
  }, []);

  useEffect(() => {
    const onSyncDone = () => {
      console.log("🔄 [profissionais] Sincronização concluída, recarregando dados...");
      if (navigator.onLine) {
        // Aguardar um pouco para garantir que o backend processou
        setTimeout(() => load(), 500);
      }
    };
    window.addEventListener("offline-sync-done", onSyncDone);
    return () => window.removeEventListener("offline-sync-done", onSyncDone);
  }, []);

  useEffect(() => {
    if (searchParams.get("novo") === "1") openNew();
  }, [searchParams]);

  const openNew = () => {
    setEditing(null);
    setForm({ name: "", specialty: "", phone: "", email: "", criar_acesso: false, perfil: "profissional" });
    setError("");
    setShowModal(true);
  };

  const openEdit = (p: Professional) => {
    setEditing(p);
    setForm({
      name: p.name,
      specialty: p.specialty || "",
      phone: p.phone || "",
      email: p.email || "",
      criar_acesso: false,
      perfil: "profissional",
    });
    setError("");
    setShowModal(true);
  };

  const save = async () => {
    if (!form.name.trim()) {
      setError("Nome é obrigatório.");
      return;
    }
    if (!form.specialty.trim()) {
      setError("Especialidade é obrigatória.");
      return;
    }
    const criarAcesso = Boolean(form.criar_acesso);
    if (criarAcesso && !form.email.trim()) {
      setError("E-mail é obrigatório para criar acesso e enviar senha.");
      return;
    }
    setSaving(true);
    setError("");
    const body: Record<string, unknown> = {
      name: form.name.trim(),
      specialty: form.specialty.trim(),
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
      active: true,
    };
    if (!editing && criarAcesso) {
      body.criar_acesso = true;
      body.perfil = form.perfil;
    }

    const isOffline = typeof navigator !== "undefined" && !navigator.onLine;
    if (isOffline) {
      try {
        const lojaSlug = getLojaSlug();
        const editingIsPendente = editing && editing.id < 0;
        if (editing && !editingIsPendente) {
          await adicionarNaFilaSync({
            tipo: "profissional",
            payload: { action: "update", id: editing.id, body: { ...body, criar_acesso: undefined } },
            lojaSlug,
          });
          const updatedList = list.map((p) =>
            p.id === editing.id
              ? { ...p, name: String(body.name), specialty: String(body.specialty), phone: (body.phone as string) ?? p.phone, email: (body.email as string) ?? p.email }
              : p
          );
          setList(updatedList);
          await salvarProfissionaisOffline(updatedList);
        } else {
          await adicionarNaFilaSync({
            tipo: "profissional",
            payload: { action: "create", body },
            lojaSlug,
          });
          const tempId = -Date.now();
          const newProf: Professional = {
            id: tempId,
            name: String(body.name),
            specialty: String(body.specialty),
            phone: (body.phone as string) ?? null,
            email: (body.email as string) ?? null,
            active: true,
          };
          const updatedList = [newProf, ...list];
          setList(updatedList);
          await salvarProfissionaisOffline(updatedList);
        }
        setShowModal(false);
        alert("Salvo offline. O profissional será sincronizado quando você estiver online.");
      } catch {
        setError("Erro ao salvar localmente. Tente novamente.");
      }
      setSaving(false);
      return;
    }

    try {
      if (editing) {
        const res = await clinicaBelezaFetch(`/professionals/${editing.id}/`, {
          method: "PUT",
          body: JSON.stringify({ ...body, criar_acesso: undefined }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({})) as Record<string, unknown>;
          const messages: string[] = [];
          if (typeof err.detail === "string") messages.push(err.detail);
          else if (Array.isArray(err.detail)) messages.push(...(err.detail as string[]));
          for (const v of Object.values(err)) {
            if (Array.isArray(v) && v.every((x) => typeof x === "string")) messages.push(...(v as string[]));
          }
          throw new Error(messages.length ? messages.join(". ") : "Erro ao atualizar");
        }
      } else {
        const res = await clinicaBelezaFetch("/professionals/", {
          method: "POST",
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({})) as Record<string, unknown>;
          const messages: string[] = [];
          if (typeof err.detail === "string") messages.push(err.detail);
          else if (Array.isArray(err.detail)) messages.push(...(err.detail as string[]));
          for (const v of Object.values(err)) {
            if (Array.isArray(v) && v.every((x) => typeof x === "string")) messages.push(...(v as string[]));
          }
          throw new Error(messages.length ? messages.join(". ") : "Erro ao cadastrar");
        }
      }
      setShowModal(false);
      load();
      if (!editing && criarAcesso) {
        alert("Profissional criado! A senha foi enviada por e-mail.");
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Erro ao salvar";
      const isNetworkError = msg.toLowerCase().includes("fetch") || msg === "Failed to fetch";
      if (isNetworkError) {
        try {
          const lojaSlug = getLojaSlug();
          if (editing && editing.id > 0) {
            await adicionarNaFilaSync({
              tipo: "profissional",
              payload: { action: "update", id: editing.id, body: { ...body, criar_acesso: undefined } },
              lojaSlug,
            });
            const updatedList = list.map((p) =>
              p.id === editing.id
                ? { ...p, name: String(body.name), specialty: String(body.specialty), phone: (body.phone as string) ?? p.phone, email: (body.email as string) ?? p.email }
                : p
            );
            setList(updatedList);
            await salvarProfissionaisOffline(updatedList);
          } else {
            await adicionarNaFilaSync({ tipo: "profissional", payload: { action: "create", body }, lojaSlug });
            const tempId = -Date.now();
            const newProf: Professional = {
              id: tempId,
              name: String(body.name),
              specialty: String(body.specialty),
              phone: (body.phone as string) ?? null,
              email: (body.email as string) ?? null,
              active: true,
            };
            const updatedList = [newProf, ...list];
            setList(updatedList);
            await salvarProfissionaisOffline(updatedList);
          }
          setShowModal(false);
          alert("Sem conexão. Profissional salvo offline e será sincronizado quando você estiver online.");
        } catch {
          setError("Sem conexão. Não foi possível salvar offline. Tente novamente.");
        }
      } else {
        setError(msg);
      }
    } finally {
      setSaving(false);
    }
  };

  const exclude = async (p: Professional) => {
    if (!confirm(`Desativar o profissional "${p.name}"?`)) return;
    try {
      await clinicaBelezaFetch(`/professionals/${p.id}/`, { method: "DELETE" });
      load();
    } catch {
      alert("Erro ao desativar.");
    }
  };

  useClinicaBelezaDark(); // Aplica tema escuro (localStorage + document.documentElement)
  const activeList = list.filter((p) => p.active);

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-white dark:from-neutral-900 dark:via-neutral-800 dark:to-neutral-900 text-gray-800 dark:text-gray-100 p-4 md:p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <button
            onClick={() => router.push(`/loja/${slug}/dashboard`)}
            className="p-2 hover:bg-white/80 dark:hover:bg-neutral-700 rounded-lg"
          >
            <ArrowLeft size={24} />
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Profissionais</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Cadastro de profissionais da clínica</p>
            {lojaOwnerInfo && (
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                <span className="text-amber-700 dark:text-amber-400">O administrador da loja aparece na tabela abaixo (linha &quot;Administrador - somente leitura&quot;) e não pode ser editado nem excluído.</span>
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <OfflineIndicator />
            <button
              onClick={openNew}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              <Plus size={20} />
              Novo Profissional
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : activeList.length === 0 ? (
          <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl p-8 text-center text-gray-500 dark:text-gray-400">
            Nenhum profissional cadastrado. Clique em &quot;Novo Profissional&quot; para começar.
          </div>
        ) : (
          <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 dark:bg-neutral-700 text-gray-600 dark:text-gray-300">
                  <tr>
                    <th className="text-left p-3">Nome</th>
                    <th className="text-left p-3">Especialidade</th>
                    <th className="text-left p-3 hidden md:table-cell">Telefone</th>
                    <th className="w-24 p-3">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {activeList.map((p) => (
                    <tr key={p.id} className="border-t border-gray-100 dark:border-neutral-700">
                      <td className="p-3 font-medium text-gray-800 dark:text-gray-200">{p.name}</td>
                      <td className="p-3 text-gray-700 dark:text-gray-300">{p.specialty || "—"}</td>
                      <td className="p-3 hidden md:table-cell text-gray-700 dark:text-gray-300">{p.phone || "—"}</td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          {p.is_administrador_vinculado ? (
                            <span className="text-xs text-amber-700 dark:text-amber-400" title="O administrador da loja não pode ser editado nem excluído">
                              Administrador (somente leitura)
                            </span>
                          ) : (
                            <>
                              <button
                                onClick={() => openEdit(p)}
                                className="p-2 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded"
                                title="Editar"
                              >
                                <Pencil size={18} />
                              </button>
                              <button
                                onClick={() => exclude(p)}
                                className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                                title="Desativar"
                              >
                                <Trash2 size={18} />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-md border dark:border-neutral-700">
            <div className="flex justify-between items-center p-4 border-b dark:border-neutral-700">
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editing ? "Editar Profissional" : "Novo Profissional"}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded">
                <X size={20} />
              </button>
            </div>
            <div className="p-4 space-y-3">
              {error && (
                <div className="p-2 rounded bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">{error}</div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="Nome completo"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Especialidade *</label>
                <input
                  value={form.specialty}
                  onChange={(e) => setForm((f) => ({ ...f, specialty: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="Ex.: Esteticista, Dermatologia"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
                <input
                  value={form.phone}
                  onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="(00) 00000-0000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">E-mail</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="email@exemplo.com"
                />
              </div>
              {!editing && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Tipo do profissional (permissões)
                    </label>
                    <select
                      value={form.perfil}
                      onChange={(e) => setForm((f) => ({ ...f, perfil: e.target.value as PerfilAcesso }))}
                      className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                    >
                      <option value="administrador">Administrador</option>
                      <option value="profissional">Profissional</option>
                      <option value="recepcao">Recepção</option>
                    </select>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Define as permissões de acesso ao sistema, se criar login abaixo.
                    </p>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.criar_acesso}
                      onChange={(e) => setForm((f) => ({ ...f, criar_acesso: e.target.checked }))}
                      className="rounded border-gray-300 dark:border-neutral-600 text-purple-600"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Criar acesso e enviar senha por e-mail (usará o tipo acima como permissão)
                    </span>
                  </label>
                </>
              )}
            </div>
            <div className="flex gap-2 p-4 border-t dark:border-neutral-700">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-gray-700 dark:text-gray-300"
              >
                Cancelar
              </button>
              <button
                onClick={save}
                disabled={saving}
                className="flex-1 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
              >
                {saving ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
