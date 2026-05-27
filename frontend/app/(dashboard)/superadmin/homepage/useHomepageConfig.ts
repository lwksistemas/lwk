'use client';

import { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/api-client';
import {
  API,
  HeroData,
  FuncionalidadeData,
  ModuloData,
  WhyUsData,
  HeroImagemData,
  EmpresaFormData,
  FilterAtivo,
  ItemType,
  BulkActionType,
  DeleteConfirm,
} from './types';

export function useHomepageConfig() {
  const [hero, setHero] = useState<HeroData | null>(null);
  const [funcionalidades, setFuncionalidades] = useState<FuncionalidadeData[]>([]);
  const [modulos, setModulos] = useState<ModuloData[]>([]);
  const [whyus, setWhyus] = useState<WhyUsData[]>([]);
  const [heroImagens, setHeroImagens] = useState<HeroImagemData[]>([]);
  const [empresaForm, setEmpresaForm] = useState<EmpresaFormData>({
    nome_empresa: 'LWK Sistemas',
    cnpj: '',
    endereco: '',
    telefone_whatsapp: '',
    mensagem_whatsapp: 'Olá! Gostaria de saber mais sobre o LWK Sistemas.',
    email_contato: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form states
  const [heroForm, setHeroForm] = useState<HeroData>({
    titulo: '',
    subtitulo: '',
    botao_texto: 'Testar grátis',
    botao_principal_ativo: true,
  });
  const [editingFunc, setEditingFunc] = useState<FuncionalidadeData | null>(null);
  const [editingMod, setEditingMod] = useState<ModuloData | null>(null);
  const [editingWhyUs, setEditingWhyUs] = useState<WhyUsData | null>(null);
  const [editingHeroImg, setEditingHeroImg] = useState<HeroImagemData | null>(null);
  const [showAddFunc, setShowAddFunc] = useState(false);
  const [showAddMod, setShowAddMod] = useState(false);
  const [showAddWhyUs, setShowAddWhyUs] = useState(false);
  const [showAddHeroImg, setShowAddHeroImg] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<DeleteConfirm | null>(null);

  // Busca e filtros
  const [searchFunc, setSearchFunc] = useState('');
  const [searchMod, setSearchMod] = useState('');
  const [searchWhyUs, setSearchWhyUs] = useState('');
  const [searchHeroImg, setSearchHeroImg] = useState('');
  const [filterFuncAtivo, setFilterFuncAtivo] = useState<FilterAtivo>('all');
  const [filterModAtivo, setFilterModAtivo] = useState<FilterAtivo>('all');
  const [filterWhyUsAtivo, setFilterWhyUsAtivo] = useState<FilterAtivo>('all');
  const [filterHeroImgAtivo, setFilterHeroImgAtivo] = useState<FilterAtivo>('all');

  // Seleção em lote
  const [selectedFunc, setSelectedFunc] = useState<number[]>([]);
  const [selectedMod, setSelectedMod] = useState<number[]>([]);
  const [selectedWhyUs, setSelectedWhyUs] = useState<number[]>([]);
  const [selectedHeroImg, setSelectedHeroImg] = useState<number[]>([]);

  const showMsg = useCallback((type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [heroRes, funcRes, modRes, whyusRes, heroImgRes, empresaRes] = await Promise.all([
        apiClient.get(API.hero),
        apiClient.get(API.funcionalidades),
        apiClient.get(API.modulos),
        apiClient.get(API.whyus),
        apiClient.get(API.heroImagens),
        apiClient.get(API.empresa).catch(() => ({ data: null })),
      ]);

      const heroList = Array.isArray(heroRes.data) ? heroRes.data : heroRes.data?.results ?? [];
      const firstHero = heroList[0];
      if (firstHero) {
        setHero(firstHero);
        setHeroForm({
          titulo: firstHero.titulo,
          subtitulo: firstHero.subtitulo,
          botao_texto: firstHero.botao_texto || 'Testar grátis',
          botao_principal_ativo: firstHero.botao_principal_ativo !== false,
        });
      } else {
        setHero(null);
        setHeroForm({ titulo: '', subtitulo: '', botao_texto: 'Testar grátis', botao_principal_ativo: true });
      }

      const funcList = Array.isArray(funcRes.data) ? funcRes.data : funcRes.data?.results ?? [];
      const modList = Array.isArray(modRes.data) ? modRes.data : modRes.data?.results ?? [];
      const whyusList = Array.isArray(whyusRes.data) ? whyusRes.data : whyusRes.data?.results ?? [];
      const heroImgList = Array.isArray(heroImgRes.data) ? heroImgRes.data : heroImgRes.data?.results ?? [];

      setFuncionalidades(funcList);
      setModulos(modList);
      setWhyus(whyusList);
      setHeroImagens(heroImgList);

      if (empresaRes.data) {
        const emp = empresaRes.data;
        setEmpresaForm({
          nome_empresa: emp.nome_empresa || 'LWK Sistemas',
          cnpj: emp.cnpj || '',
          endereco: emp.endereco || '',
          telefone_whatsapp: emp.telefone_whatsapp || '',
          mensagem_whatsapp: emp.mensagem_whatsapp || 'Olá! Gostaria de saber mais sobre o LWK Sistemas.',
          email_contato: emp.email_contato || '',
        });
      }
    } catch {
      setMessage({ type: 'error', text: 'Erro ao carregar dados' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // === SAVE FUNCTIONS ===

  const saveHero = async () => {
    if (!heroForm.titulo.trim()) { showMsg('error', 'Título é obrigatório'); return; }
    setSaving(true);
    try {
      const payload = {
        titulo: heroForm.titulo.trim(),
        subtitulo: heroForm.subtitulo?.trim() || '',
        botao_texto: heroForm.botao_texto?.trim() || 'Testar grátis',
        botao_principal_ativo: heroForm.botao_principal_ativo !== false,
      };
      if (hero?.id) {
        await apiClient.patch(`${API.hero}${hero.id}/`, payload);
        showMsg('success', 'Hero atualizado!');
      } else {
        await apiClient.post(API.hero, { ...payload, ativo: true });
        showMsg('success', 'Hero criado!');
      }
      loadData();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao salvar hero');
    } finally {
      setSaving(false);
    }
  };

  const saveEmpresa = async () => {
    setSaving(true);
    try {
      await apiClient.post(API.empresa, empresaForm);
      showMsg('success', 'Dados da empresa salvos!');
      loadData();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao salvar dados da empresa');
    } finally {
      setSaving(false);
    }
  };

  const saveFuncionalidade = async (data: FuncionalidadeData) => {
    if (!data.titulo.trim()) { showMsg('error', 'Título é obrigatório'); return; }
    if (!data.descricao?.trim()) { showMsg('error', 'Descrição é obrigatória'); return; }
    setSaving(true);
    try {
      if (data.id) {
        await apiClient.patch(`${API.funcionalidades}${data.id}/`, data);
        showMsg('success', 'Funcionalidade atualizada!');
      } else {
        await apiClient.post(API.funcionalidades, { ...data, ativo: true, ordem: 0 });
        showMsg('success', 'Funcionalidade criada!');
      }
      setEditingFunc(null);
      setShowAddFunc(false);
      loadData();
    } catch (err: unknown) {
      const e = err as { response?: { data?: Record<string, unknown> } };
      const d = e.response?.data;
      const msg = typeof d?.detail === 'string' ? d.detail
        : (Array.isArray(d?.titulo) ? d.titulo[0] : null)
          || (Array.isArray(d?.descricao) ? d.descricao[0] : null)
          || 'Erro ao salvar';
      showMsg('error', String(msg));
    } finally {
      setSaving(false);
    }
  };

  const saveModulo = async (data: ModuloData) => {
    if (!data.nome.trim()) { showMsg('error', 'Nome é obrigatório'); return; }
    setSaving(true);
    try {
      if (data.id) {
        await apiClient.patch(`${API.modulos}${data.id}/`, data);
        showMsg('success', 'Módulo atualizado!');
      } else {
        await apiClient.post(API.modulos, { ...data, ativo: true, ordem: 0 });
        showMsg('success', 'Módulo criado!');
      }
      setEditingMod(null);
      setShowAddMod(false);
      loadData();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const saveWhyUs = async (data: WhyUsData) => {
    if (!data.titulo.trim()) { showMsg('error', 'Título é obrigatório'); return; }
    setSaving(true);
    try {
      if (data.id) {
        await apiClient.patch(`${API.whyus}${data.id}/`, data);
        showMsg('success', 'Benefício atualizado!');
      } else {
        await apiClient.post(API.whyus, { ...data, ativo: true, ordem: 0 });
        showMsg('success', 'Benefício criado!');
      }
      setEditingWhyUs(null);
      setShowAddWhyUs(false);
      loadData();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const saveHeroImagem = async (data: HeroImagemData) => {
    if (!data.imagem.trim()) { showMsg('error', 'URL da imagem é obrigatória'); return; }
    setSaving(true);
    try {
      if (data.id) {
        await apiClient.patch(`${API.heroImagens}${data.id}/`, data);
        showMsg('success', 'Imagem atualizada!');
      } else {
        await apiClient.post(API.heroImagens, { ...data, ativo: true, ordem: 0 });
        showMsg('success', 'Imagem criada!');
      }
      setEditingHeroImg(null);
      setShowAddHeroImg(false);
      loadData();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const deleteItem = async () => {
    if (!deleteConfirm) return;
    setSaving(true);
    try {
      const endpointMap: Record<ItemType, string> = {
        func: API.funcionalidades,
        mod: API.modulos,
        whyus: API.whyus,
        heroimg: API.heroImagens,
      };
      await apiClient.delete(`${endpointMap[deleteConfirm.type]}${deleteConfirm.id}/`);
      showMsg('success', 'Item excluído!');
      setDeleteConfirm(null);
      loadData();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao excluir');
    } finally {
      setSaving(false);
    }
  };

  const reorderItem = async (type: ItemType, id: number, direction: 'up' | 'down') => {
    setSaving(true);
    try {
      const itemsMap: Record<ItemType, { id?: number; ordem?: number }[]> = {
        func: funcionalidades,
        mod: modulos,
        whyus: whyus,
        heroimg: heroImagens,
      };
      const items = itemsMap[type];
      const currentIndex = items.findIndex((item) => item.id === id);
      if (currentIndex === -1) return;

      const targetIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
      if (targetIndex < 0 || targetIndex >= items.length) return;

      const currentItem = items[currentIndex];
      const targetItem = items[targetIndex];

      const endpointMap: Record<ItemType, string> = {
        func: API.funcionalidades,
        mod: API.modulos,
        whyus: API.whyus,
        heroimg: API.heroImagens,
      };
      const endpoint = endpointMap[type];
      await Promise.all([
        apiClient.patch(`${endpoint}${currentItem.id}/`, { ordem: targetItem.ordem }),
        apiClient.patch(`${endpoint}${targetItem.id}/`, { ordem: currentItem.ordem }),
      ]);

      showMsg('success', 'Ordem atualizada!');
      loadData();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao reordenar');
    } finally {
      setSaving(false);
    }
  };

  const bulkAction = async (type: ItemType, action: BulkActionType) => {
    const selectedMap: Record<ItemType, number[]> = {
      func: selectedFunc,
      mod: selectedMod,
      whyus: selectedWhyUs,
      heroimg: selectedHeroImg,
    };
    const selected = selectedMap[type];
    if (selected.length === 0) { showMsg('error', 'Nenhum item selecionado'); return; }

    if (action === 'excluir' && !confirm(`Tem certeza que deseja excluir ${selected.length} itens?`)) return;

    setSaving(true);
    try {
      const endpointMap: Record<ItemType, string> = {
        func: API.funcionalidades,
        mod: API.modulos,
        whyus: API.whyus,
        heroimg: API.heroImagens,
      };
      const endpoint = endpointMap[type];

      if (action === 'excluir') {
        await Promise.all(selected.map(id => apiClient.delete(`${endpoint}${id}/`)));
        showMsg('success', `${selected.length} itens excluídos!`);
      } else {
        const ativo = action === 'ativar';
        await Promise.all(selected.map(id => apiClient.patch(`${endpoint}${id}/`, { ativo })));
        showMsg('success', `${selected.length} itens ${ativo ? 'ativados' : 'desativados'}!`);
      }

      const clearMap: Record<ItemType, () => void> = {
        func: () => setSelectedFunc([]),
        mod: () => setSelectedMod([]),
        whyus: () => setSelectedWhyUs([]),
        heroimg: () => setSelectedHeroImg([]),
      };
      clearMap[type]();
      loadData();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao executar ação em lote');
    } finally {
      setSaving(false);
    }
  };

  // === FILTERS ===

  const filteredFuncionalidades = funcionalidades.filter((f) => {
    const matchSearch = f.titulo.toLowerCase().includes(searchFunc.toLowerCase()) ||
                       f.descricao.toLowerCase().includes(searchFunc.toLowerCase());
    const matchFilter = filterFuncAtivo === 'all' ||
                       (filterFuncAtivo === 'ativo' && f.ativo !== false) ||
                       (filterFuncAtivo === 'inativo' && f.ativo === false);
    return matchSearch && matchFilter;
  });

  const filteredModulos = modulos.filter((m) => {
    const matchSearch = m.nome.toLowerCase().includes(searchMod.toLowerCase()) ||
                       m.descricao.toLowerCase().includes(searchMod.toLowerCase()) ||
                       (m.slug && m.slug.toLowerCase().includes(searchMod.toLowerCase()));
    const matchFilter = filterModAtivo === 'all' ||
                       (filterModAtivo === 'ativo' && m.ativo !== false) ||
                       (filterModAtivo === 'inativo' && m.ativo === false);
    return matchSearch && matchFilter;
  });

  const filteredWhyUs = whyus.filter((w) => {
    const matchSearch = w.titulo.toLowerCase().includes(searchWhyUs.toLowerCase()) ||
                       (w.descricao && w.descricao.toLowerCase().includes(searchWhyUs.toLowerCase()));
    const matchFilter = filterWhyUsAtivo === 'all' ||
                       (filterWhyUsAtivo === 'ativo' && w.ativo !== false) ||
                       (filterWhyUsAtivo === 'inativo' && w.ativo === false);
    return matchSearch && matchFilter;
  });

  const filteredHeroImagens = heroImagens.filter((h) => {
    const matchSearch = (h.titulo || '').toLowerCase().includes(searchHeroImg.toLowerCase());
    const matchFilter = filterHeroImgAtivo === 'all' ||
                       (filterHeroImgAtivo === 'ativo' && h.ativo !== false) ||
                       (filterHeroImgAtivo === 'inativo' && h.ativo === false);
    return matchSearch && matchFilter;
  });

  // === SELECTION TOGGLES ===

  const toggleSelectFunc = (id: number) => setSelectedFunc(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  const toggleSelectAllFunc = () => setSelectedFunc(prev => prev.length === filteredFuncionalidades.length ? [] : filteredFuncionalidades.map(f => f.id!));
  const toggleSelectMod = (id: number) => setSelectedMod(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  const toggleSelectAllMod = () => setSelectedMod(prev => prev.length === filteredModulos.length ? [] : filteredModulos.map(m => m.id!));
  const toggleSelectWhyUs = (id: number) => setSelectedWhyUs(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  const toggleSelectAllWhyUs = () => setSelectedWhyUs(prev => prev.length === filteredWhyUs.length ? [] : filteredWhyUs.map(w => w.id!));
  const toggleSelectHeroImg = (id: number) => setSelectedHeroImg(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  const toggleSelectAllHeroImg = () => setSelectedHeroImg(prev => prev.length === filteredHeroImagens.length ? [] : filteredHeroImagens.map(h => h.id!));

  return {
    // Data
    hero, heroForm, setHeroForm,
    funcionalidades: filteredFuncionalidades,
    modulos: filteredModulos,
    whyus: filteredWhyUs,
    heroImagens: filteredHeroImagens,
    empresaForm, setEmpresaForm,

    // UI state
    loading, saving, message,
    editingFunc, setEditingFunc,
    editingMod, setEditingMod,
    editingWhyUs, setEditingWhyUs,
    editingHeroImg, setEditingHeroImg,
    showAddFunc, setShowAddFunc,
    showAddMod, setShowAddMod,
    showAddWhyUs, setShowAddWhyUs,
    showAddHeroImg, setShowAddHeroImg,
    deleteConfirm, setDeleteConfirm,

    // Search & filters
    searchFunc, setSearchFunc, filterFuncAtivo, setFilterFuncAtivo,
    searchMod, setSearchMod, filterModAtivo, setFilterModAtivo,
    searchWhyUs, setSearchWhyUs, filterWhyUsAtivo, setFilterWhyUsAtivo,
    searchHeroImg, setSearchHeroImg, filterHeroImgAtivo, setFilterHeroImgAtivo,

    // Selection
    selectedFunc, toggleSelectFunc, toggleSelectAllFunc,
    selectedMod, toggleSelectMod, toggleSelectAllMod,
    selectedWhyUs, toggleSelectWhyUs, toggleSelectAllWhyUs,
    selectedHeroImg, toggleSelectHeroImg, toggleSelectAllHeroImg,

    // Actions
    loadData, saveHero, saveEmpresa, saveFuncionalidade, saveModulo,
    saveWhyUs, saveHeroImagem, deleteItem, reorderItem, bulkAction,
  };
}
