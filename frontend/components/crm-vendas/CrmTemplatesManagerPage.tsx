'use client';

import { useEffect, useMemo, useState, useCallback, useRef, memo, type RefObject } from 'react';
import type { LucideIcon } from 'lucide-react';
import { AlignCenter, AlignJustify, AlignLeft, AlignRight, Plus, Edit2, Trash2, X, Star } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { fetchAllPaginatedResults, normalizeListResponse, getCrmApiErrorDetail } from '@/lib/crm-utils';
import {
  familiaCss,
  juntarFolhasDoTemplate,
  lerLetraDoTemplate,
  LETRA_PADRAO,
  separarFolhasDoTemplate,
  TAMANHOS_LETRA,
  textoVisivelDoTemplate,
  TIPOS_LETRA,
  type LetraDoTemplate,
} from '@/lib/crm-proposta-template-legenda';
import {
  aplicarAlinhamento,
  aplicarFonte,
  editorParaTexto,
  textoParaEditor,
  type Alinhamento,
} from '@/lib/crm-proposta-template-formatacao';
import { useToast } from '@/components/ui/Toast';

export interface CrmTemplateRecord {
  id: number;
  nome: string;
  conteudo: string;
  prestadora?: number | null;
  prestadora_nome?: string | null;
  is_padrao: boolean;
  ativo: boolean;
  created_at?: string;
  updated_at?: string;
}

interface PrestadoraOption {
  id: number;
  nome: string;
  cnpj?: string;
}

export type CrmTemplateApiSegment = 'proposta-templates' | 'contrato-templates' | 'nfse-templates';

interface CrmTemplatesManagerPageProps {
  apiSegment: CrmTemplateApiSegment;
  title: string;
  subtitle: string;
  namePlaceholder: string;
  EmptyStateIcon: LucideIcon;
  /** Proposta: cada template pertence a uma prestadora. */
  vincularPrestadora?: boolean;
}

type ModalType = 'create' | 'edit' | 'delete' | null;

const EditorFolha = memo(function EditorFolha({
  titulo,
  subtitulo,
  html,
  editorRef,
  onFocus,
  classe,
  familia,
  tamanho,
}: {
  titulo: string;
  subtitulo: string;
  html: string;
  editorRef: RefObject<HTMLDivElement | null>;
  onFocus: (editor: HTMLDivElement) => void;
  classe: string;
  familia: string;
  tamanho: number;
}) {
  return (
    <section className={`flex min-h-0 flex-col overflow-hidden rounded-lg border p-3 ${classe}`}>
      <div className="shrink-0">
        <p className="text-sm font-semibold text-gray-900 dark:text-white">{titulo}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">{subtitulo}</p>
      </div>
      <div
        ref={editorRef}
        contentEditable
        suppressContentEditableWarning
        dangerouslySetInnerHTML={{ __html: html }}
        onFocus={(evento) => {
          document.execCommand('defaultParagraphSeparator', false, 'p');
          onFocus(evento.currentTarget);
        }}
        onPaste={(evento) => {
          evento.preventDefault();
          const texto = evento.clipboardData.getData('text/plain');
          document.execCommand('insertText', false, texto);
        }}
        style={{ fontFamily: familia, fontSize: `${tamanho}pt`, lineHeight: 1.45 }}
        className="mt-2 min-h-0 flex-1 overflow-y-auto text-gray-900 outline-none dark:text-white [&_p]:m-0 [&_p]:min-h-[1.35em]"
      />
    </section>
  );
});

/**
 * CRUD unificado para templates de proposta, contrato e descrição NFS-e (rotas DRF espelhadas).
 */
export default function CrmTemplatesManagerPage({
  apiSegment,
  title,
  subtitle,
  namePlaceholder,
  EmptyStateIcon,
  vincularPrestadora = false,
}: CrmTemplatesManagerPageProps) {
  const toast = useToast();
  const base = `/crm-vendas/${apiSegment}`;
  const [templates, setTemplates] = useState<CrmTemplateRecord[]>([]);
  const [prestadoras, setPrestadoras] = useState<PrestadoraOption[]>([]);
  const [filtroPrestadora, setFiltroPrestadora] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selected, setSelected] = useState<CrmTemplateRecord | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    conteudo: '',
    prestadora: '',
    is_padrao: false,
    ativo: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [htmlPrimeira, setHtmlPrimeira] = useState('<p><br></p>');
  const [htmlSegunda, setHtmlSegunda] = useState('<p><br></p>');
  const [tipoLetra, setTipoLetra] = useState('padrao');
  const [tamanhoLetra, setTamanhoLetra] = useState(9);
  const [letraBase, setLetraBase] = useState<LetraDoTemplate>(LETRA_PADRAO);
  const editorPrimeira = useRef<HTMLDivElement>(null);
  const editorSegunda = useRef<HTMLDivElement>(null);
  const editorAtivo = useRef<HTMLDivElement | null>(null);
  const faixaSelecao = useRef<Range | null>(null);

  const loadTemplates = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<CrmTemplateRecord[] | { results: CrmTemplateRecord[] }>(`${base}/`);
      setTemplates(normalizeListResponse(res.data));
      setError(null);
    } catch (err: unknown) {
      setError(getCrmApiErrorDetail(err, 'Erro ao carregar templates.'));
    } finally {
      setLoading(false);
    }
  }, [base]);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  useEffect(() => {
    if (!vincularPrestadora) return;
    fetchAllPaginatedResults<PrestadoraOption>('/crm-vendas/contas/', { tipo: 'prestadora' })
      .then(setPrestadoras)
      .catch(() => setPrestadoras([]));
  }, [vincularPrestadora]);

  useEffect(() => {
    if (modalType !== 'create' && modalType !== 'edit') return undefined;
    const guardar = () => {
      const selecao = window.getSelection();
      const editor = editorAtivo.current;
      if (!selecao || !editor || selecao.rangeCount === 0) return;
      const faixa = selecao.getRangeAt(0);
      if (document.activeElement !== editor) return;
      if (!editor.contains(faixa.commonAncestorContainer)) return;
      faixaSelecao.current = faixa.cloneRange();
    };
    document.addEventListener('selectionchange', guardar);
    return () => document.removeEventListener('selectionchange', guardar);
  }, [modalType]);

  const focarEditor = useCallback((editor: HTMLDivElement) => {
    editorAtivo.current = editor;
  }, []);

  const exigirSelecao = () => {
    const editor = editorAtivo.current;
    const faixa = faixaSelecao.current;
    if (!editor || !faixa || faixa.collapsed) {
      toast.warning('Selecione o texto.');
      return null;
    }
    return { editor, faixa };
  };

  const mudarTipo = (tipo: string) => {
    setTipoLetra(tipo);
    const alvo = exigirSelecao();
    if (!alvo) return;
    aplicarFonte(alvo.editor, alvo.faixa, { tipo });
  };

  const mudarTamanho = (tamanho: number) => {
    setTamanhoLetra(tamanho);
    const alvo = exigirSelecao();
    if (!alvo) return;
    aplicarFonte(alvo.editor, alvo.faixa, { tamanho });
  };

  const mudarAlinhamento = (alinhamento: Alinhamento) => {
    const alvo = exigirSelecao();
    if (!alvo) return;
    aplicarAlinhamento(alvo.editor, alvo.faixa, alinhamento);
  };

  const templatesVisiveis = useMemo(() => {
    if (!vincularPrestadora || !filtroPrestadora) return templates;
    return templates.filter((t) => String(t.prestadora || '') === filtroPrestadora);
  }, [filtroPrestadora, templates, vincularPrestadora]);

  const nomePrestadora = (conta: PrestadoraOption) =>
    conta.cnpj ? `${conta.nome} — ${conta.cnpj}` : conta.nome;

  const openModal = (type: ModalType, item?: CrmTemplateRecord) => {
    setModalType(type);
    setSelected(item || null);
    const folhas = separarFolhasDoTemplate(type === 'edit' ? item?.conteudo || '' : '');
    const letra = lerLetraDoTemplate(type === 'edit' ? item?.conteudo || '' : '');
    setHtmlPrimeira(textoParaEditor(folhas.primeiraPagina));
    setHtmlSegunda(textoParaEditor(folhas.proximasPaginas));
    setLetraBase(letra);
    setTipoLetra('padrao');
    setTamanhoLetra(9);
    editorAtivo.current = null;
    faixaSelecao.current = null;
    if (type === 'edit' && item) {
      setFormData({
        nome: item.nome || '',
        conteudo: item.conteudo || '',
        prestadora: item.prestadora ? String(item.prestadora) : '',
        is_padrao: item.is_padrao ?? false,
        ativo: item.ativo ?? true,
      });
    } else if (type === 'create') {
      setFormData({
        nome: '',
        conteudo: '',
        prestadora: filtroPrestadora,
        is_padrao: false,
        ativo: true,
      });
    }
  };

  const closeModal = () => {
    setModalType(null);
    setSelected(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.nome.trim()) {
      toast.warning('Nome é obrigatório');
      return;
    }
    if (vincularPrestadora && !formData.prestadora) {
      toast.warning('Selecione a empresa prestadora');
      return;
    }
    try {
      setSubmitting(true);
      const payload: Record<string, unknown> = {
        nome: formData.nome.trim(),
        conteudo: apiSegment === 'proposta-templates'
          ? juntarFolhasDoTemplate(
              editorPrimeira.current ? editorParaTexto(editorPrimeira.current) : '',
              editorSegunda.current ? editorParaTexto(editorSegunda.current) : '',
              letraBase,
            )
          : formData.conteudo,
        is_padrao: formData.is_padrao,
        ativo: formData.ativo,
      };
      if (vincularPrestadora) {
        payload.prestadora = parseInt(formData.prestadora, 10);
      }
      if (modalType === 'create') {
        await apiClient.post(`${base}/`, payload);
      } else if (modalType === 'edit' && selected) {
        await apiClient.put(`${base}/${selected.id}/`, payload);
      }
      await loadTemplates();
      closeModal();
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao salvar.'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selected) return;
    try {
      setSubmitting(true);
      await apiClient.delete(`${base}/${selected.id}/`);
      await loadTemplates();
      closeModal();
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao excluir.'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleMarcarPadrao = async (id: number) => {
    try {
      await apiClient.post(`${base}/${id}/marcar_padrao/`);
      await loadTemplates();
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao marcar como padrão.'));
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
        <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{title}</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{subtitle}</p>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-end gap-3">
          {vincularPrestadora && (
            <div className="flex flex-col gap-0.5 min-w-[16rem]">
              <label htmlFor="filtro-prestadora-template" className="text-xs text-gray-500 dark:text-gray-400">
                Prestadora
              </label>
              <select
                id="filtro-prestadora-template"
                value={filtroPrestadora}
                onChange={(e) => setFiltroPrestadora(e.target.value)}
                className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              >
                <option value="">Todas</option>
                {prestadoras.map((conta) => (
                  <option key={conta.id} value={conta.id}>
                    {nomePrestadora(conta)}
                  </option>
                ))}
              </select>
            </div>
          )}
          <button
            type="button"
            onClick={() => openModal('create')}
            className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm"
          >
            <Plus size={18} />
            <span>Novo Template</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {templatesVisiveis.length === 0 ? (
          <div className="col-span-full py-12 text-center text-gray-500 dark:text-gray-400 bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c]">
            <EmptyStateIcon size={48} className="mx-auto mb-3 opacity-30" />
            <p className="font-medium">Nenhum template cadastrado</p>
            <p className="text-sm mt-1">Clique em &quot;Novo Template&quot; para criar</p>
          </div>
        ) : (
          templatesVisiveis.map((t) => (
            <div
              key={t.id}
              className="bg-white dark:bg-[#16325c] rounded-lg shadow border border-gray-200 dark:border-[#0d1f3c] p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  {t.nome}
                  {t.is_padrao && (
                    <span title="Template padrão">
                      <Star size={16} className="text-yellow-500 fill-yellow-500" />
                    </span>
                  )}
                </h3>
                <div className="flex gap-1">
                  {!t.is_padrao && (
                    <button
                      type="button"
                      onClick={() => handleMarcarPadrao(t.id)}
                      className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                      aria-label="Marcar como padrão"
                    >
                      <Star size={16} />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => openModal('edit', t)}
                    className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                    aria-label="Editar"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => openModal('delete', t)}
                    className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400"
                    aria-label="Excluir"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              {vincularPrestadora && (
                <p className="text-xs font-medium text-[#0176d3] dark:text-blue-300 mb-1">
                  {t.prestadora_nome || 'Sem prestadora'}
                </p>
              )}
              <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
                {textoVisivelDoTemplate(t.conteudo) || 'Sem conteúdo'}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    t.ativo
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {t.ativo ? 'Ativo' : 'Inativo'}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {(modalType === 'create' || modalType === 'edit') && (
        <>
          <div className="fixed inset-0 bg-black/50 z-[80]" onClick={() => !submitting && closeModal()} />
          <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
            <div className={`flex w-full flex-col bg-white dark:bg-gray-800 rounded-lg shadow-xl ${apiSegment === 'proposta-templates' ? 'h-[min(860px,92vh)] w-[min(1240px,96vw)] overflow-hidden' : 'max-h-[92vh] max-w-2xl overflow-y-auto'}`}>
              <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {modalType === 'create' ? 'Novo Template' : 'Editar Template'}
                </h2>
                <button type="button" onClick={() => !submitting && closeModal()} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                  <X size={20} />
                </button>
              </div>
              <form onSubmit={handleSubmit} className={`p-5 ${apiSegment === 'proposta-templates' ? 'flex min-h-0 flex-1 flex-col gap-3' : 'space-y-4'}`}>
                <div className={apiSegment === 'proposta-templates' ? 'grid shrink-0 gap-4 lg:grid-cols-[minmax(16rem,1.2fr)_minmax(14rem,1fr)_auto] lg:items-end' : 'space-y-4'}>
                  {vincularPrestadora && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Empresa prestadora *
                      </label>
                      <select
                        value={formData.prestadora}
                        onChange={(e) => setFormData((f) => ({ ...f, prestadora: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        required
                      >
                        <option value="">Selecione a empresa prestadora</option>
                        {prestadoras.map((conta) => (
                          <option key={conta.id} value={conta.id}>
                            {nomePrestadora(conta)}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
                    <input
                      type="text"
                      value={formData.nome}
                      onChange={(e) => setFormData((f) => ({ ...f, nome: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                      placeholder={namePlaceholder}
                      required
                    />
                  </div>
                  <div className="flex items-center gap-4 pb-2">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.is_padrao}
                        onChange={(e) => setFormData((f) => ({ ...f, is_padrao: e.target.checked }))}
                        className="rounded"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Marcar como padrão</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.ativo}
                        onChange={(e) => setFormData((f) => ({ ...f, ativo: e.target.checked }))}
                        className="rounded"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Ativo</span>
                    </label>
                  </div>
                </div>
                {apiSegment === 'proposta-templates' ? (
                  <div className="flex min-h-0 flex-1 flex-col gap-3">
                    <div className="flex shrink-0 flex-wrap items-end gap-3">
                      <label className="block min-w-40 text-sm">
                        <span className="mb-1 block font-medium text-gray-700 dark:text-gray-300">Tipo de letra</span>
                        <select
                          value={tipoLetra}
                          onChange={(evento) => mudarTipo(evento.target.value)}
                          className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                        >
                          {TIPOS_LETRA.map((tipo) => (
                            <option key={tipo.id} value={tipo.id}>{tipo.nome}</option>
                          ))}
                        </select>
                      </label>
                      <label className="block w-28 text-sm">
                        <span className="mb-1 block font-medium text-gray-700 dark:text-gray-300">Tamanho da letra</span>
                        <select
                          value={tamanhoLetra}
                          onChange={(evento) => mudarTamanho(Number(evento.target.value))}
                          className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                        >
                          {TAMANHOS_LETRA.map((tamanho) => (
                            <option key={tamanho} value={tamanho}>{tamanho}</option>
                          ))}
                        </select>
                      </label>
                      <div className="flex gap-1 pb-0.5">
                        {([
                          ['left', 'Alinhar à esquerda', AlignLeft],
                          ['center', 'Centralizar', AlignCenter],
                          ['right', 'Alinhar à direita', AlignRight],
                          ['justify', 'Justificar', AlignJustify],
                        ] as const).map(([alinhamento, rotulo, Icone]) => (
                          <button
                            key={alinhamento}
                            type="button"
                            title={rotulo}
                            aria-label={rotulo}
                            onMouseDown={(evento) => evento.preventDefault()}
                            onClick={() => mudarAlinhamento(alinhamento)}
                            className="rounded-lg border border-gray-300 p-2 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                          >
                            <Icone size={16} />
                          </button>
                        ))}
                      </div>
                    </div>
                    <p className="shrink-0 text-xs text-gray-500 dark:text-gray-400">
                      Selecione o texto. A letra e o alinhamento mudam só nesse trecho.
                    </p>
                    <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-2">
                      <EditorFolha
                        titulo="Primeira página"
                        subtitulo="Abaixo de Mensalidades seguintes"
                        html={htmlPrimeira}
                        editorRef={editorPrimeira}
                        onFocus={focarEditor}
                        classe="border-[#1B365D]/30 bg-[#1B365D]/10 dark:border-blue-400/30 dark:bg-blue-950/40"
                        familia={familiaCss(letraBase.tipo)}
                        tamanho={letraBase.tamanho}
                      />
                      <EditorFolha
                        titulo="Segunda página e as próximas"
                        subtitulo="Recursos e condições"
                        html={htmlSegunda}
                        editorRef={editorSegunda}
                        onFocus={focarEditor}
                        classe="border-gray-300 bg-gray-50 dark:border-gray-600 dark:bg-gray-900/50"
                        familia={familiaCss(letraBase.tipo)}
                        tamanho={letraBase.tamanho}
                      />
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Conteúdo</label>
                    <textarea
                      value={formData.conteudo}
                      onChange={(e) => setFormData((f) => ({ ...f, conteudo: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                      rows={10}
                      placeholder="Conteúdo do template..."
                    />
                  </div>
                )}
                <div className={`flex gap-2 pt-1 lg:justify-end ${apiSegment === 'proposta-templates' ? 'shrink-0' : ''}`}>
                  <button type="button" onClick={() => !submitting && closeModal()} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg lg:min-w-36">
                    Cancelar
                  </button>
                  <button type="submit" disabled={submitting} className="px-6 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg disabled:opacity-50 lg:min-w-36">
                    {submitting ? 'Salvando...' : 'Salvar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </>
      )}

      {modalType === 'delete' && selected && (
        <>
          <div className="fixed inset-0 bg-black/50 z-[80]" onClick={() => !submitting && closeModal()} />
          <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full">
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Excluir Template</h2>
                <button type="button" onClick={() => !submitting && closeModal()} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                  <X size={20} />
                </button>
              </div>
              <div className="p-6">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Deseja excluir o template &quot;{selected.nome}&quot;? Esta ação não pode ser desfeita.
                </p>
                <div className="flex gap-2">
                  <button type="button" onClick={() => !submitting && closeModal()} className="flex-1 px-4 py-2 border rounded-lg">
                    Cancelar
                  </button>
                  <button type="button" onClick={handleDelete} disabled={submitting} className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50">
                    {submitting ? 'Excluindo...' : 'Excluir'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
