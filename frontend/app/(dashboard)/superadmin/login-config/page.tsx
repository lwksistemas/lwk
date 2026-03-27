'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
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
  logo: string;
  login_background: string;
  cor_primaria: string;
  cor_secundaria: string;
  titulo: string;
  subtitulo: string;
}

function LoginConfigContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tipo = (searchParams.get('tipo') || 'superadmin') as 'superadmin' | 'suporte';
  
  const [config, setConfig] = useState<LoginConfig>({
    tipo,
    logo: '',
    login_background: '',
    cor_primaria: tipo === 'superadmin' ? '#10B981' : '#3B82F6',
    cor_secundaria: tipo === 'superadmin' ? '#059669' : '#2563EB',
    titulo: tipo === 'superadmin' ? 'Superadmin' : 'Suporte',
    subtitulo: tipo === 'superadmin' ? 'Acesso administrativo' : 'Central de suporte',
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadConfig();
  }, [tipo]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(`/superadmin/login-config-sistema/?tipo=${tipo}`);
      setConfig(res.data);
    } catch (err) {
      console.error('Erro ao carregar configuração:', err);
    } finally {
      setLoading(false);
    }
  };

  const showMsg = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (config.id) {
        await apiClient.patch(`/superadmin/login-config-sistema/${config.id}/`, config);
        showMsg('success', 'Configuração atualizada com sucesso!');
      } else {
        const res = await apiClient.post('/superadmin/login-config-sistema/', config);
        setConfig(res.data);
        showMsg('success', 'Configuração criada com sucesso!');
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showMsg('error', e.response?.data?.detail || 'Erro ao salvar configuração');
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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto p-6">
        <div className="mb-6">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push('/superadmin/homepage')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar
          </Button>
          
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Configurar Login {tipo === 'superadmin' ? 'Superadmin' : 'Suporte'}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Personalize a tela de login de {tipo === 'superadmin' ? '/superadmin/login' : '/suporte/login'}
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
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Textos</CardTitle>
                <CardDescription>
                  Título e subtítulo exibidos na tela de login
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Título</Label>
                  <Input
                    value={config.titulo}
                    onChange={(e) => setConfig({ ...config, titulo: e.target.value })}
                    placeholder={tipo === 'superadmin' ? 'Superadmin' : 'Suporte'}
                  />
                </div>
                <div>
                  <Label>Subtítulo</Label>
                  <Input
                    value={config.subtitulo}
                    onChange={(e) => setConfig({ ...config, subtitulo: e.target.value })}
                    placeholder={tipo === 'superadmin' ? 'Acesso administrativo' : 'Central de suporte'}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cores</CardTitle>
                <CardDescription>
                  Cores primária e secundária da interface
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Cor Primária</Label>
                  <div className="flex gap-2">
                    <Input
                      type="color"
                      value={config.cor_primaria}
                      onChange={(e) => setConfig({ ...config, cor_primaria: e.target.value })}
                      className="w-20 h-10"
                    />
                    <Input
                      value={config.cor_primaria}
                      onChange={(e) => setConfig({ ...config, cor_primaria: e.target.value })}
                      placeholder="#10B981"
                    />
                  </div>
                </div>
                <div>
                  <Label>Cor Secundária</Label>
                  <div className="flex gap-2">
                    <Input
                      type="color"
                      value={config.cor_secundaria}
                      onChange={(e) => setConfig({ ...config, cor_secundaria: e.target.value })}
                      className="w-20 h-10"
                    />
                    <Input
                      value={config.cor_secundaria}
                      onChange={(e) => setConfig({ ...config, cor_secundaria: e.target.value })}
                      placeholder="#059669"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Imagens</CardTitle>
                <CardDescription>
                  Logo e imagem de fundo da tela de login
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ImageUpload
                  label="Logo"
                  description="Logo exibida na tela de login"
                  value={config.logo}
                  onChange={(url) => setConfig({ ...config, logo: url })}
                  maxSize={2}
                  aspectRatio="16:9"
                />
                
                <ImageUpload
                  label="Imagem de Fundo"
                  description="Imagem de fundo da tela de login (opcional)"
                  value={config.login_background}
                  onChange={(url) => setConfig({ ...config, login_background: url })}
                  maxSize={5}
                  aspectRatio="16:9"
                />
              </CardContent>
            </Card>

            <Button onClick={handleSave} disabled={saving} className="w-full">
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Salvando...' : 'Salvar Configuração'}
            </Button>
          </div>

          <div className="sticky top-6">
            <Card>
              <CardHeader>
                <CardTitle>Preview</CardTitle>
                <CardDescription>
                  Visualização da tela de login
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div 
                  className="rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700"
                  style={{
                    backgroundImage: config.login_background ? `url(${config.login_background})` : 'none',
                    backgroundColor: config.login_background ? 'transparent' : '#f3f4f6',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                  }}
                >
                  <div className="bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm p-8 min-h-[400px] flex flex-col items-center justify-center">
                    {config.logo && (
                      <img 
                        src={config.logo} 
                        alt="Logo" 
                        className="h-16 mb-6 object-contain"
                      />
                    )}
                    <h2 
                      className="text-2xl font-bold mb-2"
                      style={{ color: config.cor_primaria }}
                    >
                      {config.titulo || (tipo === 'superadmin' ? 'Superadmin' : 'Suporte')}
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400 mb-6">
                      {config.subtitulo || (tipo === 'superadmin' ? 'Acesso administrativo' : 'Central de suporte')}
                    </p>
                    <div className="w-full max-w-xs space-y-3">
                      <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                      <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                      <button
                        className="w-full h-10 rounded-lg text-white font-medium"
                        style={{ backgroundColor: config.cor_primaria }}
                      >
                        Entrar
                      </button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginConfigPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Carregando...</p>
      </div>
    }>
      <LoginConfigContent />
    </Suspense>
  );
}
