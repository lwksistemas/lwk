'use client';

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
import { Home, RefreshCw, Save } from 'lucide-react';
import CloudinaryConfig from '@/components/superadmin/CloudinaryConfig';
import { ImageUpload } from '@/components/ImageUpload';
import { FuncionalidadeForm } from '@/components/superadmin/homepage/FuncionalidadeForm';
import { ModuloForm } from '@/components/superadmin/homepage/ModuloForm';
import { WhyUsForm } from '@/components/superadmin/homepage/WhyUsForm';

import { useHomepageConfig } from './useHomepageConfig';
import { HeroImagensTab } from './HeroImagensTab';
import { EmpresaTab } from './EmpresaTab';
import { ListSectionCard } from './ListSectionCard';

export default function HomepageConfigPage() {
  const config = useHomepageConfig();

  if (config.loading && !config.hero && config.funcionalidades.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Carregando...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 dark:bg-zinc-950">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <a href="/superadmin/dashboard" className="flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
            </a>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <Home className="w-7 h-7" />
                Configurar Homepage v2.0
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Textos do banner, imagens de fundo (carrossel), funcionalidades e módulos da página inicial.
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={config.loadData} disabled={config.loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${config.loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>

        {/* Message */}
        {config.message && (
          <div className={`mb-4 p-4 rounded-lg ${
            config.message.type === 'success'
              ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
              : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
          }`}>
            {config.message.text}
          </div>
        )}

        <Tabs defaultValue="hero-imagens" className="space-y-4">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="hero-imagens">🖼️ Imagens</TabsTrigger>
            <TabsTrigger value="funcionalidades">Funcionalidades</TabsTrigger>
            <TabsTrigger value="modulos">Módulos</TabsTrigger>
            <TabsTrigger value="whyus">WhyUs</TabsTrigger>
            <TabsTrigger value="empresa">🏢 Empresa</TabsTrigger>
            <TabsTrigger value="login">Login</TabsTrigger>
            <TabsTrigger value="cloudinary">Cloudinary</TabsTrigger>
          </TabsList>

          {/* Hero Imagens */}
          <TabsContent value="hero-imagens">
            <HeroImagensTab
              items={config.heroImagens}
              searchValue={config.searchHeroImg}
              onSearchChange={config.setSearchHeroImg}
              filterValue={config.filterHeroImgAtivo}
              onFilterChange={config.setFilterHeroImgAtivo}
              selectedIds={config.selectedHeroImg}
              onToggleSelect={config.toggleSelectHeroImg}
              onToggleSelectAll={config.toggleSelectAllHeroImg}
              onBulkAction={(action) => config.bulkAction('heroimg', action)}
              onReorder={(id, direction) => config.reorderItem('heroimg', id, direction)}
              onEdit={(item) => config.setEditingHeroImg(item)}
              onDelete={(id, name) => config.setDeleteConfirm({ type: 'heroimg', id, nome: name })}
              onAdd={() => config.setShowAddHeroImg(true)}
              saving={config.saving}
            />
          </TabsContent>

          {/* Funcionalidades */}
          <TabsContent value="funcionalidades">
            <ListSectionCard
              title="Funcionalidades"
              description="Destaques exibidos na homepage (título, descrição, ícone)"
              addLabel="Nova"
              onAdd={() => config.setShowAddFunc(true)}
              items={config.funcionalidades}
              searchValue={config.searchFunc}
              onSearchChange={config.setSearchFunc}
              filterValue={config.filterFuncAtivo}
              onFilterChange={config.setFilterFuncAtivo}
              selectedIds={config.selectedFunc}
              onToggleSelect={config.toggleSelectFunc}
              onToggleSelectAll={config.toggleSelectAllFunc}
              onBulkAction={(action) => config.bulkAction('func', action)}
              onReorder={(id, direction) => config.reorderItem('func', id, direction)}
              onEdit={(item) => config.setEditingFunc(item as any)}
              onDelete={(id, name) => config.setDeleteConfirm({ type: 'func', id, nome: name })}
              renderItem={(f: any) => (
                <>
                  <p className="font-medium">{f.titulo}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{f.descricao}</p>
                  {f.icone && <span className="text-xs text-gray-500">Ícone: {f.icone}</span>}
                </>
              )}
              getItemName={(f: any) => f.titulo}
              searchPlaceholder="Buscar por título ou descrição..."
              emptyMessage={
                config.searchFunc || config.filterFuncAtivo !== 'all'
                  ? 'Nenhuma funcionalidade encontrada com os filtros aplicados.'
                  : 'Nenhuma funcionalidade. Clique em Nova para adicionar.'
              }
              saving={config.saving}
            />
          </TabsContent>

          {/* Módulos */}
          <TabsContent value="modulos">
            <ListSectionCard
              title="Módulos do Sistema"
              description="Sistemas disponíveis com links para login (slug = /loja/slug/login)"
              addLabel="Novo"
              onAdd={() => config.setShowAddMod(true)}
              items={config.modulos}
              searchValue={config.searchMod}
              onSearchChange={config.setSearchMod}
              filterValue={config.filterModAtivo}
              onFilterChange={config.setFilterModAtivo}
              selectedIds={config.selectedMod}
              onToggleSelect={config.toggleSelectMod}
              onToggleSelectAll={config.toggleSelectAllMod}
              onBulkAction={(action) => config.bulkAction('mod', action)}
              onReorder={(id, direction) => config.reorderItem('mod', id, direction)}
              onEdit={(item) => config.setEditingMod(item as any)}
              onDelete={(id, name) => config.setDeleteConfirm({ type: 'mod', id, nome: name })}
              renderItem={(m: any) => (
                <>
                  <p className="font-medium">{m.nome}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{m.descricao}</p>
                  {m.slug && <p className="text-xs text-gray-500">/loja/{m.slug}/login</p>}
                </>
              )}
              getItemName={(m: any) => m.nome}
              searchPlaceholder="Buscar por nome, descrição ou slug..."
              emptyMessage={
                config.searchMod || config.filterModAtivo !== 'all'
                  ? 'Nenhum módulo encontrado com os filtros aplicados.'
                  : 'Nenhum módulo. Clique em Novo para adicionar.'
              }
              saving={config.saving}
            />
          </TabsContent>

          {/* WhyUs */}
          <TabsContent value="whyus">
            <ListSectionCard
              title="Benefícios WhyUs"
              description='Benefícios exibidos na seção "Por que usar o LWKS?"'
              addLabel="Novo"
              onAdd={() => config.setShowAddWhyUs(true)}
              items={config.whyus}
              searchValue={config.searchWhyUs}
              onSearchChange={config.setSearchWhyUs}
              filterValue={config.filterWhyUsAtivo}
              onFilterChange={config.setFilterWhyUsAtivo}
              selectedIds={config.selectedWhyUs}
              onToggleSelect={config.toggleSelectWhyUs}
              onToggleSelectAll={config.toggleSelectAllWhyUs}
              onBulkAction={(action) => config.bulkAction('whyus', action)}
              onReorder={(id, direction) => config.reorderItem('whyus', id, direction)}
              onEdit={(item) => config.setEditingWhyUs(item as any)}
              onDelete={(id, name) => config.setDeleteConfirm({ type: 'whyus', id, nome: name })}
              renderItem={(w: any) => (
                <>
                  <p className="font-medium">{w.titulo}</p>
                  {w.descricao && <p className="text-sm text-gray-600 dark:text-gray-400">{w.descricao}</p>}
                  {w.icone && <span className="text-xs text-gray-500">Ícone: {w.icone}</span>}
                </>
              )}
              getItemName={(w: any) => w.titulo}
              searchPlaceholder="Buscar por título ou descrição..."
              emptyMessage={
                config.searchWhyUs || config.filterWhyUsAtivo !== 'all'
                  ? 'Nenhum benefício encontrado com os filtros aplicados.'
                  : 'Nenhum benefício. Clique em Novo para adicionar.'
              }
              saving={config.saving}
            />
          </TabsContent>

          {/* Empresa */}
          <TabsContent value="empresa">
            <EmpresaTab
              empresaForm={config.empresaForm}
              setEmpresaForm={config.setEmpresaForm}
              onSave={config.saveEmpresa}
              saving={config.saving}
            />
          </TabsContent>

          {/* Login */}
          <TabsContent value="login">
            <div className="grid gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Configurar Telas de Login</CardTitle>
                  <CardDescription>Configure as telas de login do Superadmin e Suporte (logos, cores, textos)</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid sm:grid-cols-2 gap-4">
                    <Link href="/superadmin/login-config?tipo=superadmin">
                      <Button variant="outline" className="w-full h-auto py-6 flex flex-col gap-2">
                        <div className="text-lg font-semibold">Login Superadmin</div>
                        <div className="text-sm text-gray-500">Configurar /superadmin/login</div>
                      </Button>
                    </Link>
                    <Link href="/superadmin/login-config?tipo=suporte">
                      <Button variant="outline" className="w-full h-auto py-6 flex flex-col gap-2">
                        <div className="text-lg font-semibold">Login Suporte</div>
                        <div className="text-sm text-gray-500">Configurar /suporte/login</div>
                      </Button>
                    </Link>
                  </div>
                  <div className="mt-4 p-4 bg-stone-100 dark:bg-zinc-900/50 rounded-lg border border-stone-200 dark:border-zinc-700">
                    <p className="text-sm text-stone-700 dark:text-stone-300">
                      💡 As configurações de login permitem personalizar logos, cores de fundo,
                      textos e imagens das telas de autenticação, similar às configurações das lojas.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Cloudinary */}
          <TabsContent value="cloudinary">
            <CloudinaryConfig />
          </TabsContent>
        </Tabs>

        {/* Modals */}
        <Modal isOpen={config.showAddFunc || !!config.editingFunc} onClose={() => { config.setShowAddFunc(false); config.setEditingFunc(null); }}>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">{config.editingFunc ? 'Editar Funcionalidade' : 'Nova Funcionalidade'}</h3>
            <FuncionalidadeForm
              key={config.editingFunc?.id ?? 'new'}
              initial={config.editingFunc ?? { titulo: '', descricao: '', icone: '' }}
              onSave={config.saveFuncionalidade}
              onCancel={() => { config.setShowAddFunc(false); config.setEditingFunc(null); }}
              saving={config.saving}
            />
          </div>
        </Modal>

        <Modal isOpen={config.showAddMod || !!config.editingMod} onClose={() => { config.setShowAddMod(false); config.setEditingMod(null); }}>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">{config.editingMod ? 'Editar Módulo' : 'Novo Módulo'}</h3>
            <ModuloForm
              key={config.editingMod?.id ?? 'new'}
              initial={config.editingMod ?? { nome: '', descricao: '', slug: '', icone: '' }}
              onSave={config.saveModulo}
              onCancel={() => { config.setShowAddMod(false); config.setEditingMod(null); }}
              saving={config.saving}
            />
          </div>
        </Modal>

        <Modal isOpen={config.showAddWhyUs || !!config.editingWhyUs} onClose={() => { config.setShowAddWhyUs(false); config.setEditingWhyUs(null); }}>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">{config.editingWhyUs ? 'Editar Benefício' : 'Novo Benefício'}</h3>
            <WhyUsForm
              key={config.editingWhyUs?.id ?? 'new'}
              initial={config.editingWhyUs ?? { titulo: '', descricao: '', icone: '✓' }}
              onSave={config.saveWhyUs}
              onCancel={() => { config.setShowAddWhyUs(false); config.setEditingWhyUs(null); }}
              saving={config.saving}
            />
          </div>
        </Modal>

        <Modal isOpen={config.showAddHeroImg || !!config.editingHeroImg} onClose={() => { config.setShowAddHeroImg(false); config.setEditingHeroImg(null); }}>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">{config.editingHeroImg ? 'Editar imagem do carrossel' : 'Nova imagem do carrossel'}</h3>
            <div className="space-y-4">
              <div>
                <Label>Título (opcional)</Label>
                <Input
                  value={config.editingHeroImg?.titulo ?? ''}
                  onChange={(e) => config.setEditingHeroImg(prev => prev ? { ...prev, titulo: e.target.value } : { imagem: '', titulo: e.target.value })}
                  placeholder="Ex: Banner Principal"
                />
              </div>
              <ImageUpload
                label="Imagem"
                description="Imagem de fundo do Hero (recomendado: 1920x1080px)"
                value={config.editingHeroImg?.imagem ?? ''}
                onChange={(url) => config.setEditingHeroImg(prev => prev ? { ...prev, imagem: url } : { imagem: url, titulo: '' })}
                maxSize={5}
                aspectRatio="16:9"
              />
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => { config.setShowAddHeroImg(false); config.setEditingHeroImg(null); }}>
                  Cancelar
                </Button>
                <Button onClick={() => config.editingHeroImg && config.saveHeroImagem(config.editingHeroImg)} disabled={config.saving || !config.editingHeroImg?.imagem}>
                  <Save className="w-4 h-4 mr-2" />
                  {config.saving ? 'Salvando...' : 'Salvar'}
                </Button>
              </div>
            </div>
          </div>
        </Modal>

        <Modal isOpen={!!config.deleteConfirm} onClose={() => config.setDeleteConfirm(null)}>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-2">Excluir?</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Tem certeza que deseja excluir &quot;{config.deleteConfirm?.nome}&quot;?
            </p>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => config.setDeleteConfirm(null)}>Cancelar</Button>
              <Button variant="destructive" onClick={config.deleteItem} disabled={config.saving}>
                {config.saving ? 'Excluindo...' : 'Excluir'}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
}
