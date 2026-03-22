'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Save, TestTube, CheckCircle, XCircle, ExternalLink } from 'lucide-react';
import apiClient from '@/lib/api-client';

interface CloudinaryConfigData {
  id?: number;
  cloud_name: string;
  api_key: string;
  api_secret?: string;
  api_secret_masked?: string;
  enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

export default function CloudinaryConfig() {
  const [config, setConfig] = useState<CloudinaryConfigData>({
    cloud_name: '',
    api_key: '',
    api_secret: '',
    enabled: false,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/superadmin/cloudinary-config/');
      setConfig(res.data);
    } catch (err) {
      console.error('Erro ao carregar configuração:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const showMsg = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const testConnection = async () => {
    if (!config.cloud_name || !config.api_key || !config.api_secret) {
      showMsg('error', 'Preencha todas as credenciais antes de testar');
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      const res = await apiClient.post('/superadmin/cloudinary-config/test/', {
        cloud_name: config.cloud_name,
        api_key: config.api_key,
        api_secret: config.api_secret,
      });

      setTestResult({
        success: res.data.success,
        message: res.data.message || 'Conexão bem-sucedida!',
      });
    } catch (err: unknown) {
      const e = err as {
        response?: { data?: { detail?: string; error?: string } };
      };
      setTestResult({
        success: false,
        message:
          e.response?.data?.detail ||
          e.response?.data?.error ||
          'Falha ao conectar',
      });
    } finally {
      setTesting(false);
    }
  };

  const saveConfig = async () => {
    if (!config.cloud_name || !config.api_key) {
      showMsg('error', 'Cloud Name e API Key são obrigatórios');
      return;
    }

    setSaving(true);
    try {
      const payload: Partial<CloudinaryConfigData> = {
        cloud_name: config.cloud_name,
        api_key: config.api_key,
        enabled: config.enabled,
      };

      // Só enviar api_secret se foi alterado
      if (config.api_secret && config.api_secret.trim()) {
        payload.api_secret = config.api_secret;
      }

      const res = await apiClient.post('/superadmin/cloudinary-config/', payload);
      
      showMsg('success', res.data.message || 'Configuração salva com sucesso!');
      loadConfig(); // Recarregar para pegar o masked secret
    } catch (err: unknown) {
      const e = err as {
        response?: { data?: { detail?: string; error?: string } };
      };
      showMsg(
        'error',
        e.response?.data?.detail ||
          e.response?.data?.error ||
          'Erro ao salvar configuração'
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500">Carregando configuração...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Configuração do Cloudinary
          <a
            href="https://cloudinary.com/users/register/free"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </CardTitle>
        <CardDescription>
          Configure as credenciais do Cloudinary para armazenar imagens da homepage.
          O Heroku não persiste uploads - use Cloudinary para armazenamento permanente.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {message && (
          <div
            className={`p-4 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
            }`}
          >
            {message.text}
          </div>
        )}

        <div className="space-y-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
            <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
              Como obter as credenciais:
            </h4>
            <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800 dark:text-blue-200">
              <li>
                Acesse{' '}
                <a
                  href="https://cloudinary.com/users/register/free"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline"
                >
                  cloudinary.com
                </a>{' '}
                e crie uma conta gratuita
              </li>
              <li>Após login, vá para o Dashboard</li>
              <li>Copie: Cloud Name, API Key e API Secret</li>
              <li>Cole aqui e clique em &quot;Testar Conexão&quot;</li>
              <li>Se funcionar, ative e salve</li>
            </ol>
          </div>

          <div>
            <Label htmlFor="cloud_name">Cloud Name</Label>
            <Input
              id="cloud_name"
              value={config.cloud_name}
              onChange={(e) =>
                setConfig((c) => ({ ...c, cloud_name: e.target.value }))
              }
              placeholder="Ex: dxxxxxxxx"
            />
          </div>

          <div>
            <Label htmlFor="api_key">API Key</Label>
            <Input
              id="api_key"
              value={config.api_key}
              onChange={(e) =>
                setConfig((c) => ({ ...c, api_key: e.target.value }))
              }
              placeholder="Ex: 123456789012345"
            />
          </div>

          <div>
            <Label htmlFor="api_secret">
              API Secret
              {config.api_secret_masked && (
                <span className="text-xs text-gray-500 ml-2">
                  (atual: {config.api_secret_masked})
                </span>
              )}
            </Label>
            <Input
              id="api_secret"
              type="password"
              value={config.api_secret || ''}
              onChange={(e) =>
                setConfig((c) => ({ ...c, api_secret: e.target.value }))
              }
              placeholder={
                config.api_secret_masked
                  ? 'Deixe em branco para manter o atual'
                  : 'Ex: AbCdEfGhIjKlMnOpQrStUvWxYz'
              }
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="enabled"
              checked={config.enabled}
              onChange={(e) =>
                setConfig((c) => ({ ...c, enabled: e.target.checked }))
              }
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="enabled" className="cursor-pointer font-normal">
              Habilitar integração com Cloudinary
            </Label>
          </div>

          {testResult && (
            <div
              className={`p-4 rounded-lg flex items-start gap-3 ${
                testResult.success
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                  : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
              }`}
            >
              {testResult.success ? (
                <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              )}
              <div>
                <p className="font-medium">
                  {testResult.success ? 'Sucesso!' : 'Erro'}
                </p>
                <p className="text-sm">{testResult.message}</p>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <Button onClick={testConnection} disabled={testing} variant="outline">
              <TestTube className="w-4 h-4 mr-2" />
              {testing ? 'Testando...' : 'Testar Conexão'}
            </Button>
            <Button onClick={saveConfig} disabled={saving}>
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Salvando...' : 'Salvar Configuração'}
            </Button>
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
              Plano Gratuito do Cloudinary:
            </h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400">
              <li>25 GB de armazenamento</li>
              <li>25 GB de bandwidth/mês</li>
              <li>25.000 transformações/mês</li>
              <li>CDN global incluído</li>
            </ul>
            <p className="text-xs text-gray-500 mt-2">
              Mais que suficiente para a homepage!
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
