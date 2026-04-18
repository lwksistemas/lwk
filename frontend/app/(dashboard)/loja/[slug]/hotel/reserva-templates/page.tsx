'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FileText, Plus, Edit2, Trash2, ArrowLeft, Star, Copy } from 'lucide-react';

interface ReservaTemplate {
  id: number;
  nome: string;
  conteudo: string;
  is_padrao: boolean;
  ativo: boolean;
  created_at: string;
}

const VARIAVEIS_DISPONIVEIS = [
  { var: '{hospede}', desc: 'Nome do hóspede' },
  { var: '{quarto}', desc: 'Número do quarto' },
  { var: '{checkin}', desc: 'Data de check-in' },
  { var: '{checkout}', desc: 'Data de check-out' },
  { var: '{valor_total}', desc: 'Valor total da reserva' },
  { var: '{diarias}', desc: 'Número de diárias' },
];

export default function ReservaTemplatesPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [templates, setTemplates] = useState<ReservaTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<ReservaTemplate | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ nome: '', conteudo: '', is_padrao: false });

  const loadTemplates = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<ReservaTemplate[] | { results: ReservaTemplate[] }>('/hotel/reserva-templates/');
      setTemplates(Array.isArray(res.data) ? res.data : (res.data.results ?? []));
    } catch { setTemplates([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadTemplates(); }, [loadTemplates]);

  const openNew = () => {
    setEditing(null);
    setForm({ nome: '', conteudo: '', is_padrao: false });
    setModalOpen(true);
  };

  const openEdit = (t: ReservaTemplate) => {
    setEditing(t);
    setForm({ nome: t.nome, conteudo: t.conteudo, is_padrao: t.is_padrao });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.nome.trim() || !form.conteudo.trim()) {
      alert('Nome e conteúdo são obrigatórios.');
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        await apiClient.put(`/hotel/reserva-templates/${editing.id}/`, form);
      } else {
        await apiClient.post('/hotel/reserva-templates/', form);
      }
      setModalOpen(false);
      loadTemplates();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erro ao salvar template.');
    } finally { setSaving(false); }
  };

  const handleDelete = async (t: ReservaTemplate) => {
    if (!confirm(`Excluir template "${t.nome}"?`)) return;
    try {
      await apiClient.delete(`/hotel/reserva-templates/${t.id}/`);
      loadTemplates();
    } catch { alert('Erro ao excluir.'); }
  };

  const insertVar = (v: string) => {
    setForm((f) => ({ ...f, conteudo: f.conteudo + v }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <div className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/15 rounded-lg hidden sm:block"><FileText className="w-6 h-6" /></div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold">Templates de Confirmação</h1>
                <p className="text-white/80 text-xs sm:text-sm">Modelos de texto para confirmação de reserva</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link href={`/loja/${slug}/hotel/reservas`} className="px-3 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors text-sm flex items-center gap-1">
                <ArrowLeft className="w-4 h-4" /> Reservas
              </Link>
              <button onClick={openNew} className="px-3 sm:px-4 py-2 bg-white text-sky-700 font-semibold rounded-md hover:bg-sky-50 transition-colors text-sm flex items-center gap-1 shadow">
                <Plus className="w-4 h-4" /> Novo Template
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
          </div>
        ) : templates.length === 0 ? (
          <div className="text-center py-20">
            <FileText className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
            <p className="text-lg font-medium text-gray-600 dark:text-gray-400">Nenhum template cadastrado</p>
            <p className="text-sm text-gray-500 mt-1 mb-4">Crie templates para agilizar a confirmação de reservas</p>
            <button onClick={openNew} className="px-4 py-2 bg-sky-600 text-white rounded-md hover:bg-sky-700 text-sm font-medium">
              Criar Primeiro Template
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {templates.map((t) => (
              <div key={t.id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white truncate">{t.nome}</h3>
                      {t.is_padrao && (
                        <span className="shrink-0 flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
                          <Star className="w-3 h-3" /> Padrão
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 whitespace-pre-wrap">{t.conteudo}</p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button onClick={() => openEdit(t)} className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500" title="Editar">
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleDelete(t)} className="p-1.5 rounded-md hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-600" title="Excluir">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} maxWidth="2xl">
        <div className="p-6 space-y-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            {editing ? 'Editar Template' : 'Novo Template'}
          </h2>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Nome do Template *</Label>
              <Input value={form.nome} onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))} placeholder="Ex: Confirmação Padrão" />
            </div>
            <div className="space-y-2">
              <Label>Conteúdo *</Label>
              <textarea
                className="w-full min-h-[200px] px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100 text-sm"
                value={form.conteudo}
                onChange={(e) => setForm((f) => ({ ...f, conteudo: e.target.value }))}
                placeholder="Prezado(a) {hospede}, confirmamos sua reserva..."
              />
              <div className="flex flex-wrap gap-1.5 mt-2">
                <span className="text-xs text-gray-500 mr-1">Variáveis:</span>
                {VARIAVEIS_DISPONIVEIS.map((v) => (
                  <button
                    key={v.var}
                    type="button"
                    onClick={() => insertVar(v.var)}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-sky-50 dark:bg-sky-900/20 text-sky-700 dark:text-sky-300 text-xs hover:bg-sky-100 dark:hover:bg-sky-900/40 transition"
                    title={v.desc}
                  >
                    <Copy className="w-3 h-3" /> {v.var}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_padrao"
                checked={form.is_padrao}
                onChange={(e) => setForm((f) => ({ ...f, is_padrao: e.target.checked }))}
                className="h-4 w-4 text-sky-600 rounded"
              />
              <label htmlFor="is_padrao" className="text-sm text-gray-700 dark:text-gray-300">
                Usar como template padrão para novas confirmações
              </label>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setModalOpen(false)} disabled={saving}>Cancelar</Button>
            <Button onClick={handleSubmit} disabled={saving || !form.nome.trim() || !form.conteudo.trim()}>
              {saving ? 'Salvando...' : 'Salvar'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
