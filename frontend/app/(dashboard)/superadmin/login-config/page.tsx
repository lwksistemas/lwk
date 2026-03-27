'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
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
import { Save, ArrowLeft } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { ImageUpload } from '@/components/ImageUpload';

interface LoginConfig {
  id?: number;
  tipo: 'superadmin' | 'suporte';
  logo_url?: string;
  logo_secundaria_url?: string;
  titulo?: string;
  subtitulo?: string;
  cor_fundo?: string;
  imagem_fundo_url?: string;
  ativo?: boolean;
}

export default function LoginConfigPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tipo = (searchParams.get('tipo') as 'superadmin' | 'suporte') || 'superadmin';
  
  const [config, setConfig] = useState<LoginConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  const [form, setForm] = useState<LoginConfig>({
    tipo,
    logo_url: '',
    logo_secundaria_url: '',
    titulo: '',
    subtitulo: '',
    cor_fundo: '#ffffff',
    imagem_fundo_url: '',
    ativo: true,
  });

  useEffect(() => {
    loadConfig();
  }, [tipo]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(`/superadmin/login-config/?tipo=${tipo}`);
      const configs = Array.isArray(res.data) ? res.data : res.data?.results ?? [];
      const found = configs.find((c: LoginConfig) => c.tipo === tipo);
      
      if (found) {
        setConfig(found);
        setForm({
          tipo: found.tipo,
          logo_url: found.logo_url || '',
          logo_secundaria_url: found.logo_secundaria_url || '',
          titulo: found.titulo || '',
          subtitulo: found.subtitulo || '',
          cor_fundo: found.cor_fundo || '#ffffff',
          imagem_fundo_url: found.imagem_fundo_url || '',
          ativo: found.ativo !== false,
        });
      } else {
        setConfig(null);
        setForm({
          tipo,
          logo_url: '',
          logo_secundaria_url: '',
          titulo: tipo === 'superadmin' ? 'Superadmin' : 'Suporte',
          subtitulo: 'Faça login para continuar',
          cor_fundo: '#ffffff',
          imagem_fundo_url: '',
          ativo: true,
        });
      }
    } catch (err) {
      showMsg('error', 'Erro ao carregar configuração');
    } finally {
      setLoading(false);
    }
  };

  const showMsg = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      const payload = {
        tipo: form.tipo,
        logo_url: form.logo_url?.trim() || null,
        logo_secundaria_url: form.logo_secundaria_url?.trim() || null,
        titulo: form.titulo?.trim() || null,
        subtitulo: form.subtitulo?.trim() || null,
        cor_fundo: form.cor_fundo?.trim() || '#ffffff',
        imagem_fundo_url: form.imagem_fundo_url?.trim() || null,
        ativo: form.ativo !== false,
      };

      if (config?.id) {
        await apiClient.patch(`/superadmin/login-config/${config.id}/`, payload);
        showMsg('success', 'Configuração atualizada!');
      } else {
        await apiClient.post('/superadmin/login-config/', payload);
        showMsg('success', 'Configuração criada!');
      }
      
      loadConfig();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Carregando...</p>
      </div>
    );
  }

  const tipoLabel = tipo === 'superadmin' ? 'Superadmin' : 'Suporte';
  const loginUrl = tipo === 'superadmin' ? '/superadmin/login' : '/suporte/login';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto p-6">
        <div className="mb-6">
          <Link href="/superadmin/homepage">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Voltar
            </Button>
          </Link>
        </div>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Configurar Login {tipoLabel}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Personalize a tela de login em {loginUrl}
          </p>
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

        <div className="grid md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Configurações de Login</CardTitle>
              <CardDescription>
                Logos, textos e cores da tela de autenticação
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ImageUpload
                label="Logo Principal"
                description="Logo exibida no topo da tela de login"
                value={form.logo_url || ''}
                onChange={(url) => setForm((f) => ({ ...f, logo_url: url }))}
                maxSize={2}
                aspectRatio="16:9"
              />

              <ImageUpload
                label="Logo Secundária"
                description="Logo alternativa (opcional)"
                value={form.logo_secundaria_url || ''}
                onChange={(url) => setForm((f) => ({ ...f, logo_secundaria_url: url }))}
                maxSize={2}
                aspectRatio="16:9"
              />

              <div>
                <Label>Título</Label>
                <Input
                  value={form.titulo}
                  onChange={(e) => setForm((f) => ({ ...f, titulo: e.target.value }))}
                  placeholder={`Ex: ${tipoLabel}`}
                />
              </div>

              <div>
                <Label>Subtítulo</Label>
                <Input
                  value={form.subtitulo}
                  onChange={(e) => setForm((f) => ({ ...f, subtitulo: e.target.value }))}
                  placeholder="Ex: Faça login para continuar"
                />
              </div>

              <div>
                <Label>Cor de Fundo</Label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={form.cor_fundo}
                    onChange={(e) => setForm((f) => ({ ...f, cor_fundo: e.target.value }))}
                    className="w-20 h-10"
                  />
                  <Input
                    type="text"
                    value={form.cor_fundo}
                    onChange={(e) => setForm((f) => ({ ...f, cor_fundo: e.target.value }))}
                    placeholder="#ffffff"
                  />
                </div>
              </div>

              <ImageUpload
                label="Imagem de Fundo"
                description="Imagem de fundo da tela de login (opcional)"
                value={form.imagem_fundo_url || ''}
                onChange={(url) => setForm((f) => ({ ...f, imagem_fundo_url: url }))}
                maxSize={5}
                aspectRatio="16:9"
              />

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="ativo"
                  checked={form.ativo !== false}
                  onChange={(e) => setForm((f) => ({ ...f, ativo: e.target.checked }))}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <Label htmlFor="ativo" className="cursor-pointer font-normal">
                  Configuração ativa
                </Label>
              </div>

              <Button onClick={saveConfig} disabled={saving} className="w-full">
                <Save className="w-4 h-4 mr-2" />
                {saving ? 'Salvando...' : 'Salvar Configuração'}
              </Button>
            </CardContent>
          </Card>

          <div className="sticky top-6">
            <Card>
              <CardHeader>
                <CardTitle>Preview</CardTitle>
                <CardDescription>
                  Visualização aproximada da tela de login
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className="rounded-lg border p-8 min-h-[400px] flex flex-col items-center justify-center"
                  style={{
                    backgroundColor: form.cor_fundo,
                    backgroundImage: form.imagem_fundo_url ? `url(${form.imagem_fundo_url})` : undefined,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                  }}
                >
                  {form.logo_url && (
                    <img
                      src={form.logo_url}
                      alt="Logo"
                      className="max-w-[200px] max-h-[80px] object-contain mb-6"
                    />
                  )}
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-sm">
                    {form.titulo && (
                      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                        {form.titulo}
                      </h2>
                    )}
                    {form.subtitulo && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                        {form.subtitulo}
                      </p>
                    )}
                    <div className="space-y-3">
                      <div className="h-10 bg-gray-100 dark:bg-gray-700 rounded"></div>
                      <div className="h-10 bg-gray-100 dark:bg-gray-700 rounded"></div>
                      <div className="h-10 bg-blue-600 rounded"></div>
                    </div>
                  </div>
                  {form.logo_secundaria_url && (
                    <img
                      src={form.logo_secundaria_url}
                      alt="Logo Secundária"
                      className="max-w-[150px] max-h-[60px] object-contain mt-6"
                    />
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
