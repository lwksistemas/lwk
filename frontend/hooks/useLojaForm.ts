import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

export interface LojaFormData {
  nome: string;
  slug: string;
  descricao: string;
  cpf_cnpj: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  uf: string;
  tipo_loja: string;
  plano: string;
  tipo_assinatura: 'mensal' | 'anual';
  dia_vencimento: number;
  provedor_boleto_preferido: 'asaas' | 'mercadopago';
  owner_full_name: string;
  owner_username: string;
  owner_password?: string;
  owner_email: string;
  owner_telefone: string;
}

export function useLojaForm(incluirSenha: boolean = true) {
  const [formData, setFormData] = useState<LojaFormData>({
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
    provedor_boleto_preferido: 'asaas',
    owner_full_name: '',
    owner_username: '',
    owner_password: '',
    owner_email: '',
    owner_telefone: '',
  });

  const [tipos, setTipos] = useState<any[]>([]);
  const [planos, setPlanos] = useState<any[]>([]);
  const [buscarCepLoading, setBuscarCepLoading] = useState(false);
  const [buscarCnpjLoading, setBuscarCnpjLoading] = useState(false);

  useEffect(() => {
    loadTiposEPlanos();
    if (incluirSenha) {
      loadMercadoPagoDefault();
      gerarSenhaProvisoria();
    }
  }, [incluirSenha]);

  const loadMercadoPagoDefault = async () => {
    try {
      const { data } = await apiClient.get('/superadmin/mercadopago-config/');
      if (data?.use_for_boletos && data?.enabled) {
        setFormData((prev) => ({ ...prev, provedor_boleto_preferido: 'mercadopago' }));
      }
    } catch {
      // Ignora
    }
  };

  const gerarSenhaProvisoria = () => {
    const letras = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const numeros = '0123456789';
    const simbolos = '!@#$%&*';
    const todos = letras + numeros + simbolos;
    
    let senha = '';
    senha += letras[Math.floor(Math.random() * letras.length)];
    senha += numeros[Math.floor(Math.random() * numeros.length)];
    senha += simbolos[Math.floor(Math.random() * simbolos.length)];
    
    for (let i = 3; i < 8; i++) {
      senha += todos[Math.floor(Math.random() * todos.length)];
    }
    
    senha = senha.split('').sort(() => Math.random() - 0.5).join('');
    
    setFormData(prev => ({ ...prev, owner_password: senha }));
  };

  const loadTiposEPlanos = async () => {
    try {
      // Usar endpoints públicos quando não incluir senha (cadastro público)
      const baseUrl = incluirSenha ? '/superadmin' : '/superadmin/public';
      
      const [tiposRes, planosRes] = await Promise.all([
        apiClient.get(`${baseUrl}/tipos-loja/`),
        apiClient.get(`${baseUrl}/planos/`)
      ]);
      
      setTipos(tiposRes.data.results || tiposRes.data);
      setPlanos(planosRes.data.results || planosRes.data);
    } catch (error) {
      console.error('Erro ao carregar tipos e planos:', error);
    }
  };

  const loadPlanosPorTipo = async (tipoId: string) => {
    if (!tipoId) {
      setPlanos([]);
      return;
    }
    
    try {
      // Usar endpoints públicos quando não incluir senha (cadastro público)
      const baseUrl = incluirSenha ? '/superadmin' : '/superadmin/public';
      const response = await apiClient.get(`${baseUrl}/planos/por_tipo/?tipo_id=${tipoId}`);
      setPlanos(response.data);
    } catch (error) {
      console.error('Erro ao carregar planos por tipo:', error);
      setPlanos([]);
    }
  };

  const getSuggestedSlug = (_nome: string, cpfCnpj: string) => {
    const digits = (cpfCnpj || '').replace(/\D/g, '');
    if (digits.length >= 11) return digits;
    if (digits.length >= 4) return digits;
    return digits || '';
  };

  const formatCpfCnpj = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 11) {
      return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    } else {
      return numbers.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
  };

  const buscarCep = async () => {
    const cep = formData.cep.replace(/\D/g, '');
    if (cep.length !== 8) {
      alert('Informe um CEP válido com 8 dígitos.');
      return;
    }
    setBuscarCepLoading(true);
    try {
      const res = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
      if (res.ok) {
        const data = await res.json();
        if (data && !data.erro) {
          setFormData(prev => ({
            ...prev,
            logradouro: data.logradouro || prev.logradouro,
            bairro: data.bairro || prev.bairro,
            cidade: data.localidade || prev.cidade,
            uf: data.uf || prev.uf,
          }));
        }
      }
    } catch {
      alert('Erro ao consultar CEP.');
    } finally {
      setBuscarCepLoading(false);
    }
  };

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

  return {
    formData,
    setFormData,
    tipos,
    planos,
    buscarCepLoading,
    buscarCnpjLoading,
    loadPlanosPorTipo,
    getSuggestedSlug,
    formatCpfCnpj,
    buscarCep,
    buscarCnpj,
    gerarSenhaProvisoria,
  };
}
