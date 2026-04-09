'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import apiClient from '@/lib/api-client';
import { FileText, Upload, AlertCircle, CheckCircle2, Info } from 'lucide-react';

export default function ConfiguracaoNotaFiscalPage() {
  const router = useRouter();
  const { config, recarregar } = useCRMConfig();
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  const [formData, setFormData] = useState({
    provedor_nf: 'asaas' as 'asaas' | 'issnet' | 'nacional' | 'manual',
    issnet_usuario: '',
    issnet_senha: '',
    issnet_senha_certificado: '',
    codigo_servico_municipal: '1401',
    descricao_servico_padrao: 'Desenvolvimento e licenciamento de software sob demanda',
    aliquota_iss: '2.00',
    emitir_nf_automaticamente: true,
  });
  
  const [certificadoFile, setCertificadoFile] = useState<File | null>(null);

  useEffect(() => {
    if (config) {
      setFormData({
        provedor_nf: config.provedor_nf || 'asaas',
        issnet_usuario: config.issnet_usuario || '',
        issnet_senha: '',
        issnet_senha_certificado: '',
        codigo_servico_municipal: config.codigo_servico_municipal || '1401',
        descricao_servico_padrao: config.descricao_servico_padrao || 'Desenvolvimento e licenciamento de software sob demanda',
        aliquota_iss: config.aliquota_iss || '2.00',
        emitir_nf_automaticamente: config.emitir_nf_automaticamente ?? true,
      });
    }
  }, [config]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const data = new FormData();
      
      // Adicionar campos de texto
      Object.entries(formData).forEach(([key, value]) => {
        if (value !== '' && value !== null && value !== undefined) {
          data.append(key, String(value));
        }
      });
      
      // Adicionar certificado se houver
      if (certificadoFile) {
        data.append('issnet_certificado', certificadoFile);
      }

      await apiClient.patch('/crm-vendas/config/', data, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setMessage({ type: 'success', text: 'Configurações salvas com sucesso!' });
      await recarregar();
      
      // Limpar senhas após salvar
      setFormData(prev => ({
        ...prev,
        issnet_senha: '',
        issnet_senha_certificado: '',
      }));
      setCertificadoFile(null);
    } catch (error: any) {
      console.error('Erro ao salvar configurações:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Erro ao salvar configurações',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validar extensão .pfx
      if (!file.name.endsWith('.pfx')) {
        setMessage({
          type: 'error',
          text: 'Por favor, selecione um arquivo .pfx (certificado digital A1)',
        });
        return;
      }
      setCertificadoFile(file);
      setMessage(null);
    }
  };

  const provedorInfo = {
    asaas: {
      titulo: 'Asaas (Intermediário - Padrão)',
      descricao: 'Emissão através do Asaas. Mais simples, sem necessidade de certificado digital próprio.',
      campos: [],
    },
    issnet: {
      titulo: 'ISSNet - Ribeirão Preto (Direto)',
      descricao: 'Emissão direta na Prefeitura de Ribeirão Preto com o CNPJ da sua loja. Requer certificado digital A1 próprio.',
      campos: ['issnet_usuario', 'issnet_senha', 'issnet_certificado', 'issnet_senha_certificado'],
    },
    nacional: {
      titulo: 'API Nacional NFS-e (Direto)',
      descricao: 'Emissão através da API Nacional NFS-e com o CNPJ da sua loja. Em breve disponível.',
      campos: [],
    },
    manual: {
      titulo: 'Emissão Manual',
      descricao: 'Sem integração automática. Você emitirá as notas manualmente no portal da prefeitura.',
      campos: [],
    },
  };

  const camposObrigatorios = provedorInfo[formData.provedor_nf].campos;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={28} />
          Configuração de Nota Fiscal da Loja
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Configure como sua loja emitirá notas fiscais para seus clientes
        </p>
        
        <div className="mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info size={20} className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
            <div className="text-sm text-blue-800 dark:text-blue-200">
              <p className="font-medium mb-2">⚠️ Importante: Duas emissões diferentes</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li><strong>NF da sua assinatura LWK:</strong> Emitida automaticamente pela LWK Sistemas quando você paga sua mensalidade</li>
                <li><strong>NF para seus clientes:</strong> Esta configuração é para quando VOCÊ prestar serviços aos SEUS clientes</li>
              </ul>
              <p className="mt-2 text-xs">
                Cada loja tem seu próprio CNPJ e certificado digital. As configurações abaixo são exclusivas da sua loja.
              </p>
            </div>
          </div>
        </div>
      </div>

      {message && (
        <div
          className={`p-4 rounded-lg flex items-start gap-3 ${
            message.type === 'success'
              ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200'
              : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 size={20} className="shrink-0 mt-0.5" />
          ) : (
            <AlertCircle size={20} className="shrink-0 mt-0.5" />
          )}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Provedor de NF */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Provedor de Nota Fiscal
          </h2>
          
          <div className="space-y-3">
            {(Object.keys(provedorInfo) as Array<keyof typeof provedorInfo>).map((key) => {
              const info = provedorInfo[key];
              const isDisabled = key === 'nacional'; // API Nacional ainda não disponível
              
              return (
                <label
                  key={key}
                  className={`flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    formData.provedor_nf === key
                      ? 'border-[#0176d3] bg-[#e3f3ff] dark:bg-[#0176d3]/10'
                      : 'border-gray-200 dark:border-[#0d1f3c] hover:border-gray-300 dark:hover:border-gray-600'
                  } ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <input
                    type="radio"
                    name="provedor_nf"
                    value={key}
                    checked={formData.provedor_nf === key}
                    onChange={(e) => setFormData({ ...formData, provedor_nf: e.target.value as any })}
                    disabled={isDisabled}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {info.titulo}
                      {isDisabled && (
                        <span className="ml-2 text-xs text-gray-500">(Em breve)</span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {info.descricao}
                    </div>
                  </div>
                </label>
              );
            })}
          </div>
        </div>

        {/* Configurações ISSNet */}
        {formData.provedor_nf === 'issnet' && (
          <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Credenciais ISSNet
            </h2>
            
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6 flex items-start gap-3">
              <Info size={20} className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <p className="font-medium mb-1">Requisitos para emissão direta com CNPJ da sua loja:</p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>Certificado Digital A1 (e-CNPJ) válido <strong>da sua loja</strong></li>
                  <li>Credenciais de acesso ao webservice da Prefeitura <strong>no nome da sua loja</strong></li>
                  <li>Cadastro ativo no portal ISSNet de Ribeirão Preto <strong>com CNPJ da sua loja</strong></li>
                </ul>
                <p className="mt-2 text-xs font-medium">
                  ⚠️ Este certificado é diferente do certificado da LWK Sistemas usado para emitir NF da sua assinatura.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Usuário ISSNet *
                </label>
                <input
                  type="text"
                  value={formData.issnet_usuario}
                  onChange={(e) => setFormData({ ...formData, issnet_usuario: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Senha ISSNet *
                </label>
                <input
                  type="password"
                  value={formData.issnet_senha}
                  onChange={(e) => setFormData({ ...formData, issnet_senha: e.target.value })}
                  placeholder="Digite para alterar"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Certificado Digital A1 (.pfx) *
                </label>
                <div className="flex items-center gap-3">
                  <label className="flex-1 flex items-center gap-3 px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-[#0176d3] transition-colors">
                    <Upload size={20} className="text-gray-400" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {certificadoFile
                        ? certificadoFile.name
                        : config?.issnet_certificado
                        ? 'Certificado já enviado - Clique para alterar'
                        : 'Clique para selecionar o arquivo .pfx'}
                    </span>
                    <input
                      type="file"
                      accept=".pfx"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                </div>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Senha do Certificado *
                </label>
                <input
                  type="password"
                  value={formData.issnet_senha_certificado}
                  onChange={(e) => setFormData({ ...formData, issnet_senha_certificado: e.target.value })}
                  placeholder="Senha do arquivo .pfx"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                />
              </div>
            </div>
          </div>
        )}

        {/* Configurações Gerais */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Configurações Gerais
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Código do Serviço Municipal
              </label>
              <input
                type="text"
                value={formData.codigo_servico_municipal}
                onChange={(e) => setFormData({ ...formData, codigo_servico_municipal: e.target.value })}
                placeholder="Ex: 1401"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Código do serviço na lista municipal (ex: 1401 para desenvolvimento de software)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Alíquota ISS (%)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={formData.aliquota_iss}
                onChange={(e) => setFormData({ ...formData, aliquota_iss: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Descrição Padrão do Serviço
              </label>
              <textarea
                value={formData.descricao_servico_padrao}
                onChange={(e) => setFormData({ ...formData, descricao_servico_padrao: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
              />
            </div>

            <div className="md:col-span-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.emitir_nf_automaticamente}
                  onChange={(e) => setFormData({ ...formData, emitir_nf_automaticamente: e.target.checked })}
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Emitir nota fiscal automaticamente ao confirmar pagamento
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Botões */}
        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </div>
      </form>
    </div>
  );
}
