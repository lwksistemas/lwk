'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';
import { formatCurrency } from '@/lib/financeiro-helpers';

export function ModalNovaLoja({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [loading, setLoading] = useState(false);
  const [tipos, setTipos] = useState<any[]>([]);
  const [planos, setPlanos] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    nome: '',
    slug: '',
    descricao: '',
    cpf_cnpj: '',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    uf: '',
    tipo_loja: '',
    plano: '',
    tipo_assinatura: 'mensal',
    dia_vencimento: 10,
    provedor_boleto_preferido: 'asaas' as 'asaas' | 'mercadopago',
    owner_full_name: '',
    owner_username: '',
    owner_password: '',
    owner_email: '',
    owner_telefone: '',
  });
  const [showSuccess, setShowSuccess] = useState(false);
  const [createdLoja, setCreatedLoja] = useState<any>(null);
  const [urlCopied, setUrlCopied] = useState(false);
  const [buscarCepLoading, setBuscarCepLoading] = useState(false);
  const [buscarCnpjLoading, setBuscarCnpjLoading] = useState(false);

  useEffect(() => {
    loadTiposEPlanos();
    gerarSenhaProvisoria(); // Gerar senha ao abrir o modal
    loadMercadoPagoDefault();
  }, []);

  const loadMercadoPagoDefault = async () => {
    try {
      const { data } = await apiClient.get('/superadmin/mercadopago-config/');
      if (data?.use_for_boletos && data?.enabled) {
        setFormData((prev) => ({ ...prev, provedor_boleto_preferido: 'mercadopago' }));
      }
    } catch {
      // Ignora; mantém padrão Asaas
    }
  };

  const gerarSenhaProvisoria = () => {
    // Gerar senha segura: 8 caracteres com letras, números e símbolos
    const letras = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const numeros = '0123456789';
    const simbolos = '!@#$%&*';
    const todos = letras + numeros + simbolos;
    
    let senha = '';
    // Garantir pelo menos 1 letra, 1 número e 1 símbolo
    senha += letras[Math.floor(Math.random() * letras.length)];
    senha += numeros[Math.floor(Math.random() * numeros.length)];
    senha += simbolos[Math.floor(Math.random() * simbolos.length)];
    
    // Completar com caracteres aleatórios até 8 caracteres
    for (let i = 3; i < 8; i++) {
      senha += todos[Math.floor(Math.random() * todos.length)];
    }
    
    // Embaralhar a senha
    senha = senha.split('').sort(() => Math.random() - 0.5).join('');
    
    setFormData(prev => ({ ...prev, owner_password: senha }));
  };

  const loadTiposEPlanos = async () => {
    try {
      const tiposRes = await apiClient.get('/superadmin/tipos-loja/');
      setTipos(tiposRes.data.results || tiposRes.data);
      
      // Carregar todos os planos inicialmente
      const planosRes = await apiClient.get('/superadmin/planos/');
      setPlanos(planosRes.data.results || planosRes.data);
    } catch (error) {
      console.error('Erro ao carregar tipos e planos:', error);
    }
  };

  // Função para carregar planos por tipo
  const loadPlanosPorTipo = async (tipoId: string) => {
    if (!tipoId) {
      setPlanos([]);
      return;
    }
    
    try {
      const response = await apiClient.get(`/superadmin/planos/por_tipo/?tipo_id=${tipoId}`);
      setPlanos(response.data);
    } catch (error) {
      console.error('Erro ao carregar planos por tipo:', error);
      setPlanos([]);
    }
  };

  /** Sugestão de slug: nome + sufixo do CPF/CNPJ (últimos 6 do CNPJ ou 4 do CPF) para evitar URLs duplicadas. */
  const getSuggestedSlug = (nome: string, cpfCnpj: string) => {
    const base = (nome || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '') || 'loja';
    const digits = (cpfCnpj || '').replace(/\D/g, '');
    let suffix = '';
    if (digits.length >= 12) suffix = digits.slice(-6);
    else if (digits.length >= 4) suffix = digits.slice(-4);
    else if (digits.length) suffix = digits;
    return suffix ? `${base}-${suffix}` : base;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    // Formatar CEP (00000-000) ao digitar
    if (name === 'cep') {
      const digits = value.replace(/\D/g, '').slice(0, 8);
      const formatted = digits.length > 5 ? `${digits.slice(0, 5)}-${digits.slice(5)}` : digits;
      setFormData(prev => ({ ...prev, cep: formatted }));
      return;
    }
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Sugestão de slug (nome + CPF/CNPJ) para evitar duplicidade entre lojas com mesmo nome
    if (name === 'nome') {
      setFormData(prev => ({ ...prev, slug: getSuggestedSlug(value, prev.cpf_cnpj) }));
    }
    
    // Carregar planos quando tipo de app for selecionado
    if (name === 'tipo_loja' && value) {
      loadPlanosPorTipo(value);
      // Limpar plano selecionado
      setFormData(prev => ({ ...prev, plano: '' }));
    }
  };

  const formatCpfCnpj = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 11) {
      // CPF: 000.000.000-00
      return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    } else {
      // CNPJ: 00.000.000/0000-00
      return numbers.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
  };

  const handleCpfCnpjChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCpfCnpj(e.target.value);
    setFormData(prev => ({ ...prev, cpf_cnpj: formatted, slug: getSuggestedSlug(prev.nome, formatted) }));
  };

  /** Consulta CEP (ViaCEP com fallback para BrasilAPI) e preenche endereço */
  const buscarCep = async () => {
    const cep = formData.cep.replace(/\D/g, '');
    if (cep.length !== 8) {
      alert('Informe um CEP válido com 8 dígitos.');
      return;
    }
    setBuscarCepLoading(true);
    const applyViaCep = (data: { logradouro?: string; bairro?: string; localidade?: string; uf?: string }) => {
      setFormData(prev => ({
        ...prev,
        logradouro: data.logradouro || prev.logradouro,
        bairro: data.bairro || prev.bairro,
        cidade: data.localidade || prev.cidade,
        uf: data.uf || prev.uf,
      }));
    };
    const applyBrasilApi = (data: { street?: string; neighborhood?: string; city?: string; state?: string }) => {
      setFormData(prev => ({
        ...prev,
        logradouro: data.street || prev.logradouro,
        bairro: data.neighborhood || prev.bairro,
        cidade: data.city || prev.cidade,
        uf: data.state || prev.uf,
      }));
    };
    const timeoutMs = 10000;
    const fetchWithTimeout = (url: string) => {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), timeoutMs);
      return fetch(url, { signal: ctrl.signal }).finally(() => clearTimeout(t));
    };
    try {
      // 1) Tentar ViaCEP (só usa se resposta OK e JSON válido)
      try {
        const resVia = await fetchWithTimeout(`https://viacep.com.br/ws/${cep}/json/`);
        if (resVia.ok) {
          const dataVia = await resVia.json();
          if (dataVia && !dataVia.erro && dataVia.cep) {
            applyViaCep(dataVia);
            setBuscarCepLoading(false);
            return;
          }
        }
      } catch {
        // Ignora falha ViaCEP e tenta BrasilAPI
      }
      // 2) Fallback: BrasilAPI CEP
      try {
        const resBr = await fetchWithTimeout(`https://brasilapi.com.br/api/cep/v1/${cep}`);
        if (resBr.ok) {
          const dataBr = await resBr.json();
          if (dataBr && (dataBr.street ?? dataBr.city ?? dataBr.state)) {
            applyBrasilApi(dataBr);
            setBuscarCepLoading(false);
            return;
          }
        }
      } catch {
        // Falha de rede ou timeout na BrasilAPI
      }
      // Nenhuma API retornou endereço
      alert('Erro ao consultar CEP. Verifique sua conexão ou tente novamente em instantes.');
    } finally {
      setBuscarCepLoading(false);
    }
  };

  /** Consulta CNPJ via BrasilAPI e preenche nome e endereço */
  const buscarCnpj = async () => {
    const cnpj = formData.cpf_cnpj.replace(/\D/g, '');
    if (cnpj.length !== 14) {
      alert('Informe um CNPJ válido com 14 dígitos para buscar.');
      return;
    }
    setBuscarCnpjLoading(true);
    try {
      const res = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`);
      if (!res.ok) {
        alert('CNPJ não encontrado ou serviço indisponível.');
        return;
      }
      const data = await res.json();
      const formatCep = (v: string) => {
        const n = (v || '').replace(/\D/g, '');
        if (n.length >= 8) return n.slice(0, 5) + '-' + n.slice(5, 8);
        return n;
      };
      setFormData(prev => ({
        ...prev,
        nome: data.razao_social || data.nome_fantasia || prev.nome,
        cep: formatCep(data.cep) || prev.cep,
        logradouro: data.logradouro || prev.logradouro,
        numero: data.numero || prev.numero,
        complemento: data.complemento || prev.complemento,
        bairro: data.bairro || prev.bairro,
        cidade: data.municipio || prev.cidade,
        uf: data.uf || prev.uf,
        slug: getSuggestedSlug(data.razao_social || data.nome_fantasia || prev.nome, prev.cpf_cnpj),
      }));
    } catch {
      alert('Erro ao consultar CNPJ. Tente novamente.');
    } finally {
      setBuscarCnpjLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        ...formData,
        provedor_boleto_preferido: formData.provedor_boleto_preferido || 'asaas',
      };
      const response = await apiClient.post('/superadmin/lojas/', payload);
      const loja = response.data;
      setCreatedLoja(loja);
      setShowSuccess(true);
      onSuccess();
      // Fechar após animação
      setTimeout(() => {
        onClose();
      }, 3200);
    } catch (error: any) {
      console.error('Erro completo ao criar loja:', error);
      console.error('Response data:', error.response?.data);
      
      let mensagemErro = '❌ Erro ao criar loja:\n\n';
      
      if (error.response?.data) {
        // Se for um objeto com erros de validação
        if (typeof error.response.data === 'object') {
          Object.entries(error.response.data).forEach(([campo, erros]: [string, any]) => {
            if (Array.isArray(erros)) {
              mensagemErro += `• ${campo}: ${erros.join(', ')}\n`;
            } else {
              mensagemErro += `• ${campo}: ${erros}\n`;
            }
          });
        } else {
          mensagemErro += error.response.data;
        }
      } else {
        mensagemErro += 'Erro desconhecido ao criar loja';
      }
      
      alert(mensagemErro);
    } finally {
      setLoading(false);
    }
  };

  const planoSelecionado = planos.find(p => p.id === parseInt(formData.plano));
  const valorAssinatura = planoSelecionado 
    ? (formData.tipo_assinatura === 'anual' 
        ? planoSelecionado.preco_anual 
        : planoSelecionado.preco_mensal)
    : 0;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-0">
      <div className="bg-white dark:bg-gray-800 w-full h-full max-w-full max-h-full flex flex-col rounded-none shadow-2xl">
        {/* Header fixo */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-purple-900 text-white shrink-0">
          <h2 className="text-2xl font-bold">Nova Loja</h2>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 text-2xl font-bold w-10 h-10 flex items-center justify-center rounded-full hover:bg-white/10 transition"
            aria-label="Fechar"
          >
            ×
          </button>
        </div>
        
        {/* Conteúdo: formulário ou tela de sucesso (tela cheia, sem faixa lateral) */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 relative w-full">
          {showSuccess && createdLoja ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-white dark:bg-gray-800 z-10 p-8 animate-fade-in">
              <div className="flex flex-col items-center max-w-2xl text-center">
                <div className="w-20 h-20 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mb-6 animate-scale-in">
                  <span className="text-5xl text-green-600 dark:text-green-400">✓</span>
                </div>
                <h3 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">Loja criada com sucesso!</h3>
                <p className="text-lg text-purple-600 dark:text-purple-400 font-semibold mb-4">{createdLoja.nome}</p>
                
                {/* Mensagem sobre boleto e senha */}
                <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mb-4 w-full">
                  <p className="text-sm text-blue-900 dark:text-blue-300 font-medium mb-2">
                    📧 Boleto enviado para o email
                  </p>
                  <p className="text-sm text-blue-800 dark:text-blue-400">
                    A senha de acesso será enviada automaticamente para <strong>{formData.owner_email}</strong> após a confirmação do pagamento.
                  </p>
                </div>

                {/* Exibir boleto_url e pix_qr_code se disponíveis */}
                {(createdLoja.boleto_url || createdLoja.pix_qr_code) && (
                  <div className="bg-purple-50 dark:bg-purple-900/30 border border-purple-200 dark:border-purple-700 rounded-lg p-4 mb-4 w-full">
                    <p className="text-sm font-semibold text-purple-900 dark:text-purple-300 mb-3">Formas de pagamento disponíveis:</p>
                    <div className="space-y-2">
                      {createdLoja.boleto_url && (
                        <a
                          href={createdLoja.boleto_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block px-4 py-2 bg-white dark:bg-gray-700 border border-purple-300 dark:border-purple-600 rounded-md hover:bg-purple-100 dark:hover:bg-purple-800 transition text-purple-700 dark:text-purple-300 font-medium"
                        >
                          🧾 Abrir Boleto
                        </a>
                      )}
                      {createdLoja.pix_qr_code && (
                        <button
                          type="button"
                          onClick={() => {
                            // Aqui você pode abrir um modal com o QR code PIX
                            alert('QR Code PIX disponível. Implementar modal se necessário.');
                          }}
                          className="block w-full px-4 py-2 bg-white dark:bg-gray-700 border border-purple-300 dark:border-purple-600 rounded-md hover:bg-purple-100 dark:hover:bg-purple-800 transition text-purple-700 dark:text-purple-300 font-medium"
                        >
                          📱 Ver QR Code PIX
                        </button>
                      )}
                    </div>
                  </div>
                )}

                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 flex flex-wrap items-center justify-center gap-2">
                  <span>URL de acesso:</span>
                  <span className="font-mono text-gray-800 dark:text-gray-200 break-all">{typeof window !== 'undefined' ? `${window.location.origin}${createdLoja.login_page_url}` : createdLoja.login_page_url}</span>
                  {typeof window !== 'undefined' && (
                    <button
                      type="button"
                      onClick={() => {
                        const url = `${window.location.origin}${createdLoja.login_page_url}`;
                        navigator.clipboard.writeText(url);
                        setUrlCopied(true);
                        setTimeout(() => setUrlCopied(false), 2000);
                      }}
                      className="text-xs px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded hover:bg-purple-200 dark:hover:bg-purple-800 disabled:opacity-70"
                    >
                      {urlCopied ? '✓ Copiado!' : 'Copiar URL'}
                    </button>
                  )}
                </p>
                
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition font-medium mt-4"
                >
                  Fechar
                </button>
                <p className="text-xs text-gray-400 mt-4 animate-pulse">Fechando automaticamente em instantes...</p>
              </div>
            </div>
          ) : null}
          <form id="form-nova-loja" onSubmit={handleSubmit} className="space-y-6 w-full">
            {/* Seção 1: Informações Básicas */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-300">1. Informações Básicas</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Nome da Loja *
                  </label>
                  <input
                    type="text"
                    name="nome"
                    value={formData.nome}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Ex: Minha Loja Tech"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Slug (URL) – editável
                  </label>
                  <input
                    type="text"
                    name="slug"
                    value={formData.slug}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="minha-loja-123456"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">URL: /loja/{formData.slug || '…'}/login — sugestão automática; você pode editar</p>
                </div>

                <div className="flex gap-2 items-end">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      CPF ou CNPJ *
                    </label>
                    <input
                      type="text"
                      name="cpf_cnpj"
                      value={formData.cpf_cnpj}
                      onChange={handleCpfCnpjChange}
                      required
                      maxLength={18}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                      placeholder="000.000.000-00 ou 00.000.000/0000-00"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={buscarCnpj}
                    disabled={buscarCnpjLoading || formData.cpf_cnpj.replace(/\D/g, '').length !== 14}
                    className={`px-4 py-2 rounded-md whitespace-nowrap transition-all ${
                      buscarCnpjLoading || formData.cpf_cnpj.replace(/\D/g, '').length !== 14
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700 cursor-pointer'
                    }`}
                    title={
                      formData.cpf_cnpj.replace(/\D/g, '').length !== 14
                        ? 'Digite um CNPJ válido (14 dígitos)'
                        : 'Buscar dados do CNPJ na Receita Federal'
                    }
                  >
                    {buscarCnpjLoading ? 'Buscando...' : 'Buscar CNPJ'}
                  </button>
                </div>

                <div className="md:col-span-3">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Descrição
                  </label>
                  <textarea
                    name="descricao"
                    value={formData.descricao}
                    onChange={handleChange}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Descrição da loja..."
                  />
                </div>
              </div>
            </div>

            {/* Seção 2: Endereço (CEP primeiro para consulta automática) */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-300">2. Endereço</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex gap-2 items-end">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      CEP (busca automática)
                    </label>
                    <input
                      type="text"
                      name="cep"
                      value={formData.cep}
                      onChange={handleChange}
                      onBlur={() => formData.cep.replace(/\D/g, '').length === 8 && buscarCep()}
                      maxLength={9}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                      placeholder="00000-000"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={buscarCep}
                    disabled={buscarCepLoading || formData.cep.replace(/\D/g, '').length !== 8}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                    title="Buscar endereço pelo CEP"
                  >
                    {buscarCepLoading ? '...' : 'Buscar'}
                  </button>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Logradouro
                  </label>
                  <input
                    type="text"
                    name="logradouro"
                    value={formData.logradouro}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Rua, avenida..."
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Número
                    </label>
                    <input
                      type="text"
                      name="numero"
                      value={formData.numero}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                      placeholder="Nº"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Complemento
                    </label>
                    <input
                      type="text"
                      name="complemento"
                      value={formData.complemento}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                      placeholder="Sala, apto..."
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Bairro
                  </label>
                  <input
                    type="text"
                    name="bairro"
                    value={formData.bairro}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Bairro"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Cidade
                  </label>
                  <input
                    type="text"
                    name="cidade"
                    value={formData.cidade}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Cidade"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    UF
                  </label>
                  <input
                    type="text"
                    name="uf"
                    value={formData.uf}
                    onChange={handleChange}
                    maxLength={2}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500 uppercase"
                    placeholder="UF"
                  />
                </div>
              </div>
            </div>

            {/* Seção 3: Tipo de App */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-300">3. Tipo de App</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Selecione o tipo *
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {tipos.map((tipo) => (
                  <label
                    key={tipo.id}
                    className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                      formData.tipo_loja === tipo.id.toString()
                        ? 'border-purple-600 bg-purple-50 dark:bg-purple-900/20'
                        : 'border-gray-200 dark:border-gray-600 hover:border-purple-300 dark:hover:border-purple-500'
                    }`}
                  >
                    <input
                      type="radio"
                      name="tipo_loja"
                      value={tipo.id}
                      checked={formData.tipo_loja === tipo.id.toString()}
                      onChange={handleChange}
                      className="sr-only"
                    />
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-gray-900 dark:text-gray-100">{tipo.nome}</span>
                      <div
                        className="w-6 h-6 rounded-full"
                        style={{ backgroundColor: tipo.cor_primaria }}
                      />
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Seção 4: Plano e Assinatura */}
          <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-300">4. Plano e Assinatura</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Selecione o plano *
                </label>
                {!formData.tipo_loja ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    Selecione um tipo de app primeiro para ver os planos disponíveis
                  </div>
                ) : planos.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    Nenhum plano disponível para este tipo de app
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {planos.map((plano) => (
                      <label
                        key={plano.id}
                        className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                          formData.plano === plano.id.toString()
                            ? 'border-purple-600 bg-purple-50 dark:bg-purple-900/20'
                            : 'border-gray-200 dark:border-gray-600 hover:border-purple-300 dark:hover:border-purple-500'
                        }`}
                      >
                        <input
                          type="radio"
                          name="plano"
                          value={plano.id}
                          checked={formData.plano === plano.id.toString()}
                          onChange={handleChange}
                          className="sr-only"
                        />
                        <div className="text-center">
                          <h4 className="font-bold text-lg mb-2 text-gray-900 dark:text-gray-100">{plano.nome}</h4>
                          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                            {formatCurrency(plano.preco_mensal)}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">por mês</p>
                          {plano.preco_anual && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              ou {formatCurrency(plano.preco_anual)}/ano
                            </p>
                          )}
                          <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 line-clamp-2">
                            {plano.descricao}
                          </p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tipo de Assinatura *
                  </label>
                  <select
                    name="tipo_assinatura"
                    value={formData.tipo_assinatura}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  >
                    <option value="mensal">Mensal</option>
                    <option value="anual">Anual</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Dia de Vencimento *
                  </label>
                  <select
                    name="dia_vencimento"
                    value={formData.dia_vencimento}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  >
                    {Array.from({ length: 28 }, (_, i) => i + 1).map(dia => (
                      <option key={dia} value={dia}>Dia {dia}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Provedor de boleto
                </label>
                <select
                  name="provedor_boleto_preferido"
                  value={formData.provedor_boleto_preferido}
                  onChange={(e) => setFormData((prev) => ({ ...prev, provedor_boleto_preferido: e.target.value as 'asaas' | 'mercadopago' }))}
                  className="w-full max-w-xs px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="asaas">Asaas</option>
                  <option value="mercadopago">Mercado Pago</option>
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Define qual provedor gerará os boletos desta loja</p>
              </div>

              {valorAssinatura > 0 && (
                <div className="bg-purple-50 dark:bg-purple-900/30 border border-purple-200 dark:border-purple-700 rounded-lg p-4">
                  <p className="text-sm font-medium text-purple-900 dark:text-purple-300">
                    Valor da assinatura: <span className="text-xl">{formatCurrency(valorAssinatura)}</span>
                    {formData.tipo_assinatura === 'anual' && ' (pagamento anual)'}
                  </p>
                  <p className="text-xs text-purple-700 dark:text-purple-400 mt-1">
                    Vencimento todo dia {formData.dia_vencimento} do mês
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Seção 5: Usuário Administrador */}
          <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-300">5. Usuário Administrador da Loja</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome de Usuário *
                </label>
                <input
                  type="text"
                  name="owner_full_name"
                  value={formData.owner_full_name}
                  onChange={handleChange}
                  required
                  autoComplete="name"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Ex: Maria Silva Santos"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Nome completo do administrador da loja</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Usuário para acessar o sistema *
                </label>
                <input
                  type="text"
                  name="owner_username"
                  value={formData.owner_username}
                  onChange={handleChange}
                  required
                  autoComplete="username"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Ex: maria.silva ou admin_loja"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Login usado para entrar no painel da loja</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Senha Provisória *
                </label>
                <div className="flex gap-2">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      name="owner_password"
                      value={formData.owner_password}
                      onChange={handleChange}
                      required
                      minLength={6}
                      readOnly
                      className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-purple-500 focus:border-purple-500 font-mono"
                      placeholder="Gerando..."
                    />
                    <button
                      type="button"
                      onClick={() => {
                        navigator.clipboard.writeText(formData.owner_password);
                        alert('✅ Senha copiada para a área de transferência!');
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400"
                      title="Copiar senha"
                    >
                      📋
                    </button>
                  </div>
                  <button
                    type="button"
                    onClick={gerarSenhaProvisoria}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 whitespace-nowrap"
                    title="Gerar nova senha"
                  >
                    🔄 Gerar Nova
                  </button>
                </div>
                <p className="text-xs text-green-600 dark:text-green-400 mt-1 flex items-center gap-1">
                  <span>✅</span>
                  <span>Esta senha será enviada por email para o proprietário</span>
                </p>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  E-mail *
                </label>
                <input
                  type="email"
                  name="owner_email"
                  value={formData.owner_email}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="admin@loja.com"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Telefone do administrador
                </label>
                <input
                  type="tel"
                  name="owner_telefone"
                  value={formData.owner_telefone}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="(00) 00000-0000"
                />
              </div>
            </div>
          </div>

        </form>
        </div>
        
        {/* Footer fixo */}
        <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 bg-gray-50 dark:bg-gray-800 shrink-0">
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              form="form-nova-loja"
              disabled={loading}
              className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Criando...' : 'Criar Loja'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

