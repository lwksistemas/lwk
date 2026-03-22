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
import {
  Home,
  RefreshCw,
  Plus,
  Pencil,
  Trash2,
  Save,
} from 'lucide-react';
import apiClient from '@/lib/api-client';
import CloudinaryConfig from '@/components/superadmin/CloudinaryConfig';

interface HeroData {
  id?: number;
  titulo: string;
  subtitulo: string;
  botao_texto: string;
  botao_principal_ativo?: boolean;
  ativo?: boolean;
}

interface FuncionalidadeData {
  id?: number;
  titulo: string;
  descricao: string;
  icone: string;
  ordem?: number;
  ativo?: boolean;
}

interface ModuloData {
  id?: number;
  nome: string;
  descricao: string;
  slug: string;
  icone: string;
  ordem?: number;
  ativo?: boolean;
}

const API = {
  hero: '/superadmin/homepage/hero/',
  funcionalidades: '/superadmin/homepage/funcionalidades/',
  modulos: '/superadmin/homepage/modulos/',
};

export default function HomepageConfigPage() {
  const [hero, setHero] = useState<HeroData | null>(null);
  const [funcionalidades, setFuncionalidades] = useState<FuncionalidadeData[]>([]);
  const [modulos, setModulos] = useState<ModuloData[]>([]);
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
  const [showAddFunc, setShowAddFunc] = useState(false);
  const [showAddMod, setShowAddMod] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    type: 'func' | 'mod';
    id: number;
    nome: string;
  } | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [heroRes, funcRes, modRes] = await Promise.all([
        apiClient.get(API.hero),
        apiClient.get(API.funcionalidades),
        apiClient.get(API.modulos),
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
      setFuncionalidades(funcList);
      setModulos(modList);
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
        await apiClient.patch(`${API.funcionalidades}${data.id}/`, {
          titulo: data.titulo.trim(),
          descricao: data.descricao?.trim() || '',
          icone: data.icone?.trim() || '',
        });
        showMsg('success', 'Funcionalidade atualizada!');
      } else {
        await apiClient.post(API.funcionalidades, {
          titulo: data.titulo.trim(),
          descricao: data.descricao?.trim() || '',
          icone: data.icone?.trim() || '📦',
          ativo: true,
          ordem: 0,
        });
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
          || (Array.isArray(data?.icone) ? data.icone[0] : null)
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

  const deleteItem = async () => {
    if (!deleteConfirm) return;
    setSaving(true);
    try {
      if (deleteConfirm.type === 'func') {
        await apiClient.delete(`${API.funcionalidades}${deleteConfirm.id}/`);
        showMsg('success', 'Funcionalidade excluída!');
      } else {
        await apiClient.delete(`${API.modulos}${deleteConfirm.id}/`);
        showMsg('success', 'Módulo excluído!');
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
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="hero">Hero</TabsTrigger>
            <TabsTrigger value="funcionalidades">Funcionalidades</TabsTrigger>
            <TabsTrigger value="modulos">Módulos</TabsTrigger>
            <TabsTrigger value="cloudinary">Cloudinary</TabsTrigger>
          </TabsList>

          <TabsContent value="hero">
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
                <div className="space-y-3">
                  {funcionalidades.map((f) => (
                    <div
                      key={f.id}
                      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                    >
                      <div>
                        <p className="font-medium">{f.titulo}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{f.descricao}</p>
                        {f.icone && (
                          <span className="text-xs text-gray-500">Ícone: {f.icone}</span>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            setEditingFunc({
                              id: f.id,
                              titulo: f.titulo,
                              descricao: f.descricao,
                              icone: f.icone || '',
                            })
                          }
                        >
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-red-600"
                          onClick={() => setDeleteConfirm({ type: 'func', id: f.id!, nome: f.titulo })}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  {funcionalidades.length === 0 && !showAddFunc && (
                    <p className="text-gray-500 italic">Nenhuma funcionalidade. Clique em Nova para adicionar.</p>
                  )}
                </div>
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
                <div className="space-y-3">
                  {modulos.map((m) => (
                    <div
                      key={m.id}
                      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                    >
                      <div>
                        <p className="font-medium">{m.nome}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{m.descricao}</p>
                        {m.slug && (
                          <p className="text-xs text-gray-500">/loja/{m.slug}/login</p>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            setEditingMod({
                              id: m.id,
                              nome: m.nome,
                              descricao: m.descricao,
                              slug: m.slug || '',
                              icone: m.icone || '',
                            })
                          }
                        >
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-red-600"
                          onClick={() => setDeleteConfirm({ type: 'mod', id: m.id!, nome: m.nome })}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  {modulos.length === 0 && !showAddMod && (
                    <p className="text-gray-500 italic">Nenhum módulo. Clique em Novo para adicionar.</p>
                  )}
                </div>
              </CardContent>
            </Card>
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
            <FuncForm
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
            <ModForm
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

function FuncForm({
  initial,
  onSave,
  onCancel,
  saving,
}: {
  initial: FuncionalidadeData;
  onSave: (d: FuncionalidadeData) => void;
  onCancel: () => void;
  saving: boolean;
}) {
  const [form, setForm] = useState(initial);

  return (
    <div className="space-y-4">
      <div>
        <Label>Título</Label>
        <Input
          value={form.titulo}
          onChange={(e) => setForm((f) => ({ ...f, titulo: e.target.value }))}
          placeholder="Ex: CRM de Clientes"
        />
      </div>
      <div>
        <Label>Descrição</Label>
        <textarea
          className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={form.descricao}
          onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
          placeholder="Ex: Gestão completa de clientes"
        />
      </div>
      <div>
        <Label>Ícone (emoji ou nome: Users, BarChart, etc.)</Label>
        <Input
          value={form.icone}
          onChange={(e) => setForm((f) => ({ ...f, icone: e.target.value }))}
          placeholder="Ex: 👥 ou Users"
        />
      </div>
      <div className="flex gap-2">
        <Button onClick={() => onSave(form)} disabled={saving}>
          Salvar
        </Button>
        <Button variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
    </div>
  );
}

function ModForm({
  initial,
  onSave,
  onCancel,
  saving,
}: {
  initial: ModuloData;
  onSave: (d: ModuloData) => void;
  onCancel: () => void;
  saving: boolean;
}) {
  const [form, setForm] = useState(initial);

  return (
    <div className="space-y-4">
      <div>
        <Label>Nome</Label>
        <Input
          value={form.nome}
          onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
          placeholder="Ex: CRM Vendas"
        />
      </div>
      <div>
        <Label>Descrição</Label>
        <textarea
          className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={form.descricao}
          onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
          placeholder="Ex: Gestão de vendas e leads"
        />
      </div>
      <div>
        <Label>Slug (para link /loja/slug/login)</Label>
        <Input
          value={form.slug}
          onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))}
          placeholder="Ex: crm-vendas"
        />
      </div>
      <div>
        <Label>Ícone (emoji ou nome)</Label>
        <Input
          value={form.icone}
          onChange={(e) => setForm((f) => ({ ...f, icone: e.target.value }))}
          placeholder="Ex: 📊"
        />
      </div>
      <div className="flex gap-2">
        <Button onClick={() => onSave(form)} disabled={saving}>
          Salvar
        </Button>
        <Button variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
    </div>
  );
}
