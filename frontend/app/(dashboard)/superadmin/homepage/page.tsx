'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Modal } from '@/components/ui/Modal';
import { Home, RefreshCw, Plus, Save } from 'lucide-react';
import apiClient from '@/lib/api-client';
import CloudinaryConfig from '@/components/superadmin/CloudinaryConfig';
import { ImageUpload } from '@/components/ImageUpload';
import { HomepagePreview } from '@/components/superadmin/HomepagePreview';
import { BulkActionList } from '@/components/superadmin/BulkActionList';
import { FuncionalidadeForm } from '@/components/superadmin/homepage/FuncionalidadeForm';
import { ModuloForm } from '@/components/superadmin/homepage/ModuloForm';
import { WhyUsForm } from '@/components/superadmin/homepage/WhyUsForm';

interface HeroData {
  id?: number;
  titulo: string;
  subtitulo: string;
  botao_texto: string;
  botao_principal_ativo?: boolean;
  imagem?: string;
  ativo?: boolean;
}

interface FuncionalidadeData {
  id?: number;
  titulo: string;
  descricao: string;
  icone: string;
  imagem?: string;
  ordem?: number;
  ativo?: boolean;
}

interface ModuloData {
  id?: number;
  nome: string;
  descricao: string;
  slug: string;
  icone: string;
  imagem?: string;
  ordem?: number;
  ativo?: boolean;
}

interface WhyUsData {
  id?: number;
  titulo: string;
  descricao?: string;
  icone?: string;
  ordem?: number;
  ativo?: boolean;
}

const API = {
  hero: '/superadmin/homepage/hero/',
  funcionalidades: '/superadmin/homepage/funcionalidades/',
  modulos: '/superadmin/homepage/modulos/',
  whyus: '/superadmin/homepage/whyus/',
};

export default function HomepageConfigPage() {
  const [hero, setHero] = useState<HeroData | null>(null);
  const [funcionalidades, setFuncionalidades] = useState<FuncionalidadeData[]>([]);
  const [modulos, setModulos] = useState<ModuloData[]>([]);
  const [whyus, setWhyus] = useState<WhyUsData[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form states
  const [heroForm, setHeroForm] = useState<HeroData>({
    titulo: '',
    subtitulo: '',
    botao_texto: 'Testar grátis',
    botao_principal_ativo: true,
    imagem: '',
  });
  const [editingFunc, setEditingFunc] = useState<FuncionalidadeData | null>(null);
  const [editingMod, setEditingMod] = useState<ModuloData | null>(null);
  const [editingWhyUs, setEditingWhyUs] = useState<WhyUsData | null>(null);
  const [showAddFunc, setShowAddFunc] = useState(false);
  const [showAddMod, setShowAddMod] = useState(false);
  const [showAddWhyUs, setShowAddWhyUs] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    type: 'func' | 'mod' | 'whyus';
    id: number;
    nome: string;
  } | null>(null);

  // Busca e filtros
  const [searchFunc, setSearchFunc] = useState('');
  const [searchMod, setSearchMod] = useState('');
  const [searchWhyUs, setSearchWhyUs] = useState('');
  const [filterFuncAtivo, setFilterFuncAtivo] = useState<'all' | 'ativo' | 'inativo'>('all');
  const [filterModAtivo, setFilterModAtivo] = useState<'all' | 'ativo' | 'inativo'>('all');
  const [filterWhyUsAtivo, setFilterWhyUsAtivo] = useState<'all' | 'ativo' | 'inativo'>('all');
  
  // Seleção em lote
  const [selectedFunc, setSelectedFunc] = useState<number[]>([]);
  const [selectedMod, setSelectedMod] = useState<number[]>([]);
  const [selectedWhyUs, setSelectedWhyUs] = useState<number[]>([]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [heroRes, funcRes, modRes, whyusRes] = await Promise.all([
        apiClient.get(API.hero),
        apiClient.get(API.funcionalidades),
        apiClient.get(API.modulos),
        apiClient.get(API.whyus),
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
          imagem: firstHero.imagem || '',
        });
      } else {
        setHero(null);
        setHeroForm({ titulo: '', subtitulo: '', botao_texto: 'Testar grátis', botao_principal_ativo: true, imagem: '' });
      }

      const funcList = Array.isArray(funcRes.data) ? funcRes.data : funcRes.data?.results ?? [];
      const modList = Array.isArray(modRes.data) ? modRes.data : modRes.data?.results ?? [];
      const whyusList = Array.isArray(whyusRes.data) ? whyusRes.data : whyusRes.data?.results ?? [];
      setFuncionalidades(funcList);
      setModulos(modList);
      setWhyus(whyusList);
    } catch (err) {
      setMessage({ type: 'error', text: 'Erro ao carregar dados' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const showMsg = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const saveHero = async () => {
    if (!heroForm.titulo.trim()) {
      showMsg('error', 'Título é obrigatório');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        titulo: heroForm.titulo.trim(),
        subtitulo: heroForm.subtitulo?.trim() || '',
        botao_texto: heroForm.botao_texto?.trim() || 'Testar grátis',
        botao_principal_ativo: heroForm.botao_principal_ativo !== false,
        imagem: heroForm.imagem?.trim() || '',
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
      const e = err as { response?: { data?: { detail?: string }; status?: number } };
      const detail = e.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail[0] : 'Erro ao salvar hero';
      showMsg('error', String(msg));
    } finally {
      setSaving(false);
    }
  };

  const saveFuncionalidade = async (data: FuncionalidadeData) => {
    if (!data.titulo.trim()) {
      showMsg('error', 'Título é obrigatório');
      return;
    }
    if (!data.descricao?.trim()) {
      showMsg('error', 'Descrição é obrigatória');
      return;
    }
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
      const data = e.response?.data;
      const msg = typeof data?.detail === 'string'
        ? data.detail
        : (Array.isArray(data?.titulo) ? data.titulo[0] : null)
          || (Array.isArray(data?.descricao) ? data.descricao[0] : null)
          || 'Erro ao salvar';
      showMsg('error', String(msg));
    } finally {
      setSaving(false);
    }
  };

  const saveModulo = async (data: ModuloData) => {
    if (!data.nome.trim()) {
      showMsg('error', 'Nome é obrigatório');
      return;
    }
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
    if (!data.titulo.trim()) {
      showMsg('error', 'Título é obrigatório');
      return;
    }
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

  const deleteItem = async () => {
    if (!deleteConfirm) return;
    setSaving(true);
    try {
      if (deleteConfirm.type === 'func') {
        await apiClient.delete(`${API.funcionalidades}${deleteConfirm.id}/`);
        showMsg('success', 'Funcionalidade excluída!');
      } else if (deleteConfirm.type === 'mod') {
        await apiClient.delete(`${API.modulos}${deleteConfirm.id}/`);
        showMsg('success', 'Módulo excluído!');
      } else if (deleteConfirm.type === 'whyus') {
        await apiClient.delete(`${API.whyus}${deleteConfirm.id}/`);
        showMsg('success', 'Benefício excluído!');
      }
      setDeleteConfirm(null);
      loadData();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao excluir');
    } finally {
      setSaving(false);
    }
  };

  const reorderItem = async (type: 'func' | 'mod' | 'whyus', id: number, direction: 'up' | 'down') => {
    setSaving(true);
    try {
      const items = type === 'func' ? funcionalidades : type === 'mod' ? modulos : whyus;
      const currentIndex = items.findIndex((item) => item.id === id);
      if (currentIndex === -1) return;

      const targetIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
      if (targetIndex < 0 || targetIndex >= items.length) return;

      const currentItem = items[currentIndex];
      const targetItem = items[targetIndex];

      const endpoint = type === 'func' ? API.funcionalidades : type === 'mod' ? API.modulos : API.whyus;
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

  // Filtrar funcionalidades
  const filteredFuncionalidades = funcionalidades.filter((f) => {
    const matchSearch = f.titulo.toLowerCase().includes(searchFunc.toLowerCase()) ||
                       f.descricao.toLowerCase().includes(searchFunc.toLowerCase());
    const matchFilter = filterFuncAtivo === 'all' ||
                       (filterFuncAtivo === 'ativo' && f.ativo !== false) ||
                       (filterFuncAtivo === 'inativo' && f.ativo === false);
    return matchSearch && matchFilter;
  });

  // Filtrar módulos
  const filteredModulos = modulos.filter((m) => {
    const matchSearch = m.nome.toLowerCase().includes(searchMod.toLowerCase()) ||
                       m.descricao.toLowerCase().includes(searchMod.toLowerCase()) ||
                       (m.slug && m.slug.toLowerCase().includes(searchMod.toLowerCase()));
    const matchFilter = filterModAtivo === 'all' ||
                       (filterModAtivo === 'ativo' && m.ativo !== false) ||
                       (filterModAtivo === 'inativo' && m.ativo === false);
    return matchSearch && matchFilter;
  });

  // Filtrar WhyUs
  const filteredWhyUs = whyus.filter((w) => {
    const matchSearch = w.titulo.toLowerCase().includes(searchWhyUs.toLowerCase()) ||
                       (w.descricao && w.descricao.toLowerCase().includes(searchWhyUs.toLowerCase()));
    const matchFilter = filterWhyUsAtivo === 'all' ||
                       (filterWhyUsAtivo === 'ativo' && w.ativo !== false) ||
                       (filterWhyUsAtivo === 'inativo' && w.ativo === false);
    return matchSearch && matchFilter;
  });

  // Funções de seleção em lote
  const toggleSelectFunc = (id: number) => {
    setSelectedFunc(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAllFunc = () => {
    if (selectedFunc.length === filteredFuncionalidades.length) {
      setSelectedFunc([]);
    } else {
      setSelectedFunc(filteredFuncionalidades.map(f => f.id!));
    }
  };

  const toggleSelectMod = (id: number) => {
    setSelectedMod(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAllMod = () => {
    if (selectedMod.length === filteredModulos.length) {
      setSelectedMod([]);
    } else {
      setSelectedMod(filteredModulos.map(m => m.id!));
    }
  };

  const toggleSelectWhyUs = (id: number) => {
    setSelectedWhyUs(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAllWhyUs = () => {
    if (selectedWhyUs.length === filteredWhyUs.length) {
      setSelectedWhyUs([]);
    } else {
      setSelectedWhyUs(filteredWhyUs.map(w => w.id!));
    }
  };

  // Ações em lote
  const bulkAction = async (type: 'func' | 'mod' | 'whyus', action: 'ativar' | 'desativar' | 'excluir') => {
    const selected = type === 'func' ? selectedFunc : type === 'mod' ? selectedMod : selectedWhyUs;
    if (selected.length === 0) {
      showMsg('error', 'Nenhum item selecionado');
      return;
    }

    const confirmMsg = action === 'excluir' 
      ? `Tem certeza que deseja excluir ${selected.length} ${type === 'func' ? 'funcionalidades' : type === 'mod' ? 'módulos' : 'benefícios'}?`
      : `${action === 'ativar' ? 'Ativar' : 'Desativar'} ${selected.length} itens?`;
    
    if (action === 'excluir' && !confirm(confirmMsg)) {
      return;
    }

    setSaving(true);
    try {
      const endpoint = type === 'func' ? API.funcionalidades : type === 'mod' ? API.modulos : API.whyus;
      
      if (action === 'excluir') {
        await Promise.all(selected.map(id => apiClient.delete(`${endpoint}${id}/`)));
        showMsg('success', `${selected.length} itens excluídos!`);
      } else {
        const ativo = action === 'ativar';
        await Promise.all(selected.map(id => apiClient.patch(`${endpoint}${id}/`, { ativo })));
        showMsg('success', `${selected.length} itens ${action === 'ativar' ? 'ativados' : 'desativados'}!`);
      }

      if (type === 'func') setSelectedFunc([]);
      else if (type === 'mod') setSelectedMod([]);
      else setSelectedWhyUs([]);

      loadData();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao executar ação em lote');
    } finally {
      setSaving(false);
    }
  };

  if (loading && !hero && funcionalidades.length === 0 && modulos.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Carregando...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Home className="w-7 h-7" />
              Configurar Homepage
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Edite textos, funcionalidades e módulos da página inicial.
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={loadData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>

        {message && (
          <div
            className={`mb-4 p-4 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
            }`}
          >
            {message.text}
          </div>
        )}

        <Tabs defaultValue="hero" className="space-y-4">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="hero">Hero</TabsTrigger>
            <TabsTrigger value="funcionalidades">Funcionalidades</TabsTrigger>
            <TabsTrigger value="modulos">Módulos</TabsTrigger>
            <TabsTrigger value="whyus">WhyUs</TabsTrigger>
            <TabsTrigger value="login">Login</TabsTrigger>
            <TabsTrigger value="cloudinary">Cloudinary</TabsTrigger>
          </TabsList>

          <TabsContent value="hero">
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Hero Section</CardTitle>
                  <CardDescription>
                    Título, subtítulo e texto do botão principal da página inicial
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Título</Label>
                    <Input
                      value={heroForm.titulo}
                      onChange={(e) => setHeroForm((f) => ({ ...f, titulo: e.target.value }))}
                      placeholder="Ex: LWK SISTEMAS"
                    />
                  </div>
                  <div>
                    <Label>Subtítulo</Label>
                    <textarea
                      className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={heroForm.subtitulo}
                      onChange={(e) => setHeroForm((f) => ({ ...f, subtitulo: e.target.value }))}
                      placeholder="Ex: Gestão de Lojas"
                    />
                  </div>
                  
                  <ImageUpload
                    label="Imagem do Hero"
                    description="Imagem principal exibida no banner da homepage (opcional)"
                    value={heroForm.imagem || ''}
                    onChange={(url) => setHeroForm((f) => ({ ...f, imagem: url }))}
                    maxSize={5}
                    aspectRatio="16:9"
                  />
                  
                  <div>
                    <Label>Texto do botão</Label>
                    <Input
                      value={heroForm.botao_texto}
                      onChange={(e) => setHeroForm((f) => ({ ...f, botao_texto: e.target.value }))}
                      placeholder="Ex: Testar grátis"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="botao_principal_ativo"
                      checked={heroForm.botao_principal_ativo !== false}
                      onChange={(e) => setHeroForm((f) => ({ ...f, botao_principal_ativo: e.target.checked }))}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <Label htmlFor="botao_principal_ativo" className="cursor-pointer font-normal">
                      Exibir botão &quot;Testar grátis&quot; na homepage
                    </Label>
                  </div>
                  <Button onClick={saveHero} disabled={saving}>
                    <Save className="w-4 h-4 mr-2" />
                    {saving ? 'Salvando...' : 'Salvar Hero'}
                  </Button>
                </CardContent>
              </Card>
              
              <div className="sticky top-6">
                <HomepagePreview type="hero" data={heroForm} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="funcionalidades">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Funcionalidades</CardTitle>
                  <CardDescription>
                    Destaques exibidos na homepage (título, descrição, ícone)
                  </CardDescription>
                </div>
                <Button size="sm" onClick={() => setShowAddFunc(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Nova
                </Button>
              </CardHeader>
              <CardContent>
                <BulkActionList
                  items={filteredFuncionalidades}
                  searchValue={searchFunc}
                  onSearchChange={setSearchFunc}
                  filterValue={filterFuncAtivo}
                  onFilterChange={setFilterFuncAtivo}
                  selectedIds={selectedFunc}
                  onToggleSelect={toggleSelectFunc}
                  onToggleSelectAll={toggleSelectAllFunc}
                  onBulkAction={(action) => bulkAction('func', action)}
                  onReorder={(id, direction) => reorderItem('func', id, direction)}
                  onEdit={(item) => setEditingFunc(item)}
                  onDelete={(id, name) => setDeleteConfirm({ type: 'func', id, nome: name })}
                  renderItem={(f) => (
                    <>
                      <p className="font-medium">{f.titulo}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{f.descricao}</p>
                      {f.icone && (
                        <span className="text-xs text-gray-500">Ícone: {f.icone}</span>
                      )}
                    </>
                  )}
                  getItemName={(f) => f.titulo}
                  searchPlaceholder="Buscar por título ou descrição..."
                  emptyMessage={
                    searchFunc || filterFuncAtivo !== 'all'
                      ? 'Nenhuma funcionalidade encontrada com os filtros aplicados.'
                      : 'Nenhuma funcionalidade. Clique em Nova para adicionar.'
                  }
                  saving={saving}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="modulos">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Módulos do Sistema</CardTitle>
                  <CardDescription>
                    Sistemas disponíveis com links para login (slug = /loja/slug/login)
                  </CardDescription>
                </div>
                <Button size="sm" onClick={() => setShowAddMod(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Novo
                </Button>
              </CardHeader>
              <CardContent>
                <BulkActionList
                  items={filteredModulos}
                  searchValue={searchMod}
                  onSearchChange={setSearchMod}
                  filterValue={filterModAtivo}
                  onFilterChange={setFilterModAtivo}
                  selectedIds={selectedMod}
                  onToggleSelect={toggleSelectMod}
                  onToggleSelectAll={toggleSelectAllMod}
                  onBulkAction={(action) => bulkAction('mod', action)}
                  onReorder={(id, direction) => reorderItem('mod', id, direction)}
                  onEdit={(item) => setEditingMod(item)}
                  onDelete={(id, name) => setDeleteConfirm({ type: 'mod', id, nome: name })}
                  renderItem={(m) => (
                    <>
                      <p className="font-medium">{m.nome}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{m.descricao}</p>
                      {m.slug && (
                        <p className="text-xs text-gray-500">/loja/{m.slug}/login</p>
                      )}
                    </>
                  )}
                  getItemName={(m) => m.nome}
                  searchPlaceholder="Buscar por nome, descrição ou slug..."
                  emptyMessage={
                    searchMod || filterModAtivo !== 'all'
                      ? 'Nenhum módulo encontrado com os filtros aplicados.'
                      : 'Nenhum módulo. Clique em Novo para adicionar.'
                  }
                  saving={saving}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="whyus">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Benefícios WhyUs</CardTitle>
                  <CardDescription>
                    Benefícios exibidos na seção "Por que usar o LWKS?"
                  </CardDescription>
                </div>
                <Button size="sm" onClick={() => setShowAddWhyUs(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Novo
                </Button>
              </CardHeader>
              <CardContent>
                <BulkActionList
                  items={filteredWhyUs}
                  searchValue={searchWhyUs}
                  onSearchChange={setSearchWhyUs}
                  filterValue={filterWhyUsAtivo}
                  onFilterChange={setFilterWhyUsAtivo}
                  selectedIds={selectedWhyUs}
                  onToggleSelect={toggleSelectWhyUs}
                  onToggleSelectAll={toggleSelectAllWhyUs}
                  onBulkAction={(action) => bulkAction('whyus', action)}
                  onReorder={(id, direction) => reorderItem('whyus', id, direction)}
                  onEdit={(item) => setEditingWhyUs(item)}
                  onDelete={(id, name) => setDeleteConfirm({ type: 'whyus', id, nome: name })}
                  renderItem={(w) => (
                    <>
                      <p className="font-medium">{w.titulo}</p>
                      {w.descricao && (
                        <p className="text-sm text-gray-600 dark:text-gray-400">{w.descricao}</p>
                      )}
                      {w.icone && (
                        <span className="text-xs text-gray-500">Ícone: {w.icone}</span>
                      )}
                    </>
                  )}
                  getItemName={(w) => w.titulo}
                  searchPlaceholder="Buscar por título ou descrição..."
                  emptyMessage={
                    searchWhyUs || filterWhyUsAtivo !== 'all'
                      ? 'Nenhum benefício encontrado com os filtros aplicados.'
                      : 'Nenhum benefício. Clique em Novo para adicionar.'
                  }
                  saving={saving}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="login">
            <div className="grid gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Configurar Telas de Login</CardTitle>
                  <CardDescription>
                    Configure as telas de login do Superadmin e Suporte (logos, cores, textos)
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid sm:grid-cols-2 gap-4">
                    <Link href="/superadmin/login-config?tipo=superadmin">
                      <Button variant="outline" className="w-full h-auto py-6 flex flex-col gap-2">
                        <div className="text-lg font-semibold">Login Superadmin</div>
                        <div className="text-sm text-gray-500">
                          Configurar /superadmin/login
                        </div>
                      </Button>
                    </Link>
                    <Link href="/superadmin/login-config?tipo=suporte">
                      <Button variant="outline" className="w-full h-auto py-6 flex flex-col gap-2">
                        <div className="text-lg font-semibold">Login Suporte</div>
                        <div className="text-sm text-gray-500">
                          Configurar /suporte/login
                        </div>
                      </Button>
                    </Link>
                  </div>
                  <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      💡 As configurações de login permitem personalizar logos, cores de fundo, 
                      textos e imagens das telas de autenticação, similar às configurações das lojas.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="cloudinary">
            <CloudinaryConfig />
          </TabsContent>
        </Tabs>

        {/* Modal Adicionar/Editar Funcionalidade */}
        <Modal
          isOpen={showAddFunc || !!editingFunc}
          onClose={() => {
            setShowAddFunc(false);
            setEditingFunc(null);
          }}
        >
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">
              {editingFunc ? 'Editar Funcionalidade' : 'Nova Funcionalidade'}
            </h3>
            <FuncionalidadeForm
              key={editingFunc?.id ?? 'new'}
              initial={editingFunc ?? { titulo: '', descricao: '', icone: '' }}
              onSave={saveFuncionalidade}
              onCancel={() => {
                setShowAddFunc(false);
                setEditingFunc(null);
              }}
              saving={saving}
            />
          </div>
        </Modal>

        {/* Modal Adicionar/Editar Módulo */}
        <Modal
          isOpen={showAddMod || !!editingMod}
          onClose={() => {
            setShowAddMod(false);
            setEditingMod(null);
          }}
        >
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">
              {editingMod ? 'Editar Módulo' : 'Novo Módulo'}
            </h3>
            <ModuloForm
              key={editingMod?.id ?? 'new'}
              initial={editingMod ?? { nome: '', descricao: '', slug: '', icone: '' }}
              onSave={saveModulo}
              onCancel={() => {
                setShowAddMod(false);
                setEditingMod(null);
              }}
              saving={saving}
            />
          </div>
        </Modal>

        {/* Modal Adicionar/Editar WhyUs */}
        <Modal
          isOpen={showAddWhyUs || !!editingWhyUs}
          onClose={() => {
            setShowAddWhyUs(false);
            setEditingWhyUs(null);
          }}
        >
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">
              {editingWhyUs ? 'Editar Benefício' : 'Novo Benefício'}
            </h3>
            <WhyUsForm
              key={editingWhyUs?.id ?? 'new'}
              initial={editingWhyUs ?? { titulo: '', descricao: '', icone: '✓' }}
              onSave={saveWhyUs}
              onCancel={() => {
                setShowAddWhyUs(false);
                setEditingWhyUs(null);
              }}
              saving={saving}
            />
          </div>
        </Modal>

        {/* Modal Confirmar Exclusão */}
        <Modal isOpen={!!deleteConfirm} onClose={() => setDeleteConfirm(null)}>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-2">Excluir?</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Tem certeza que deseja excluir &quot;{deleteConfirm?.nome}&quot;?
            </p>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
                Cancelar
              </Button>
              <Button variant="destructive" onClick={deleteItem} disabled={saving}>
                {saving ? 'Excluindo...' : 'Excluir'}
              </Button>
            </div>
          </div>
        </Modal>

        <div className="mt-6">
          <Link href="/superadmin/dashboard">
            <Button variant="outline">← Voltar ao Dashboard</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
