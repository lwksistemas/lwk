'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ExternalLink, Home, RefreshCw, Settings } from 'lucide-react';
import apiClient, { getCurrentApiBaseUrl } from '@/lib/api-client';

interface HeroData {
  id: number;
  titulo: string;
  subtitulo: string;
  botao_texto: string;
}

interface FuncionalidadeData {
  id: number;
  titulo: string;
  descricao: string;
  icone: string;
}

interface ModuloData {
  id: number;
  nome: string;
  descricao: string;
  slug: string;
  icone: string;
}

interface HomepageData {
  hero: HeroData | null;
  funcionalidades: FuncionalidadeData[];
  modulos: ModuloData[];
}

function getAdminHomepageUrl(): string {
  const base = getCurrentApiBaseUrl();
  const adminBase = base.replace(/\/api\/?$/, '');
  return `${adminBase}/admin/homepage/`;
}

export default function HomepageConfigPage() {
  const [data, setData] = useState<HomepageData | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<HomepageData>('/homepage/');
      setData(res.data);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const adminUrl = typeof window !== 'undefined' ? getAdminHomepageUrl() : '';

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
              Edite textos, funcionalidades e módulos da página inicial pelo painel admin.
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={loadData} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
            <Button asChild>
              <a href={adminUrl} target="_blank" rel="noopener noreferrer">
                <Settings className="w-4 h-4 mr-2" />
                Abrir Admin
                <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </Button>
          </div>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Como configurar</CardTitle>
            <CardDescription>
              Clique em &quot;Abrir Admin&quot; para acessar o painel Django. Lá você pode cadastrar e editar:
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <ul className="list-disc list-inside space-y-1">
              <li><strong>Hero Section</strong> – Título, subtítulo e texto do botão principal</li>
              <li><strong>Funcionalidades</strong> – Destaques exibidos na homepage (título, descrição, ícone)</li>
              <li><strong>Módulos do Sistema</strong> – Sistemas disponíveis com links para login (ex: CRM Vendas, Clínica)</li>
            </ul>
            <p className="pt-2">
              Após salvar no admin, a página inicial será atualizada automaticamente.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pré-visualização atual</CardTitle>
            <CardDescription>
              Dados exibidos na página inicial (somente leitura)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-gray-500">Carregando...</p>
            ) : (
              <div className="space-y-6">
                {/* Hero */}
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Hero</h3>
                  {data?.hero ? (
                    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                      <p className="font-semibold text-lg">{data.hero.titulo}</p>
                      <p className="text-gray-600 dark:text-gray-300">{data.hero.subtitulo}</p>
                      <p className="text-sm text-gray-500 mt-2">Botão: {data.hero.botao_texto}</p>
                    </div>
                  ) : (
                    <p className="text-gray-400 italic">Nenhum hero cadastrado</p>
                  )}
                </div>

                {/* Funcionalidades */}
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Funcionalidades</h3>
                  {data?.funcionalidades && data.funcionalidades.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {data.funcionalidades.map((f) => (
                        <div key={f.id} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                          <p className="font-medium">{f.titulo}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{f.descricao}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-400 italic">Nenhuma funcionalidade cadastrada</p>
                  )}
                </div>

                {/* Módulos */}
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Módulos</h3>
                  {data?.modulos && data.modulos.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {data.modulos.map((m) => (
                        <div key={m.id} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                          <p className="font-medium">{m.nome}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{m.descricao}</p>
                          {m.slug && (
                            <p className="text-xs text-gray-500 mt-1">
                              Link: /loja/{m.slug}/login
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-400 italic">Nenhum módulo cadastrado</p>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="mt-6">
          <Link href="/superadmin/dashboard">
            <Button variant="outline">← Voltar ao Dashboard</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
