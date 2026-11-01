'use client';

import { useEffect, useState } from 'react';
import { X, LogIn } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { getPrimaryApiRoot } from '@/lib/api-base';

interface AcessoRapidoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AcessoRapidoModal({ isOpen, onClose }: AcessoRapidoModalProps) {
  const [tipoAcesso, setTipoAcesso] = useState<'documento' | 'atalho'>('documento');
  const [documento, setDocumento] = useState('');
  const [atalho, setAtalho] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    if (!isOpen) return;
    function tecla(evento: KeyboardEvent) {
      if (evento.key === "Escape") onClose();
    }
    document.addEventListener("keydown", tecla);
    return () => document.removeEventListener("keydown", tecla);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const formatarDocumento = (valor: string) => {
    // Remove tudo que não é número
    const numeros = valor.replace(/\D/g, '');
    
    // Limita a 14 dígitos (CNPJ)
    const limitado = numeros.slice(0, 14);
    
    // Formata CPF (11 dígitos) ou CNPJ (14 dígitos)
    if (limitado.length <= 11) {
      // CPF: 000.000.000-00
      return limitado
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    } else {
      // CNPJ: 00.000.000/0000-00
      return limitado
        .replace(/(\d{2})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1/$2')
        .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const valorFormatado = formatarDocumento(e.target.value);
    setDocumento(valorFormatado);
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setLoading(true);
    setError('');

    try {
      if (tipoAcesso === 'atalho') {
        // Buscar por atalho
        if (!atalho.trim()) {
          setError('Digite o atalho da sua loja');
          setLoading(false);
          return;
        }

        const apiUrl = getPrimaryApiRoot();
        const url = `${apiUrl}/api/superadmin/lojas/por-atalho/?atalho=${atalho.trim()}`;

        const response = await fetch(url);

        if (!response.ok) {
          if (response.status === 404) {
            setError('Nenhuma loja encontrada com este atalho');
          } else if (response.status === 429) {
            setError('Muitas tentativas agora. Aguarde um pouco e tente de novo.');
          } else {
            setError('Erro ao buscar loja. Tente novamente.');
          }
          setLoading(false);
          return;
        }

        const data = await response.json();
        const destino = data.atalho || data.slug;
        router.push(`/loja/${destino}/login?from=${atalho.trim()}`);
        
      } else {
        // Buscar por CPF/CNPJ (código original)
        const documentoLimpo = documento.replace(/\D/g, '');
        
        // Valida tamanho
        if (documentoLimpo.length !== 11 && documentoLimpo.length !== 14) {
          setError('Digite um CPF (11 dígitos) ou CNPJ (14 dígitos) válido');
          setLoading(false);
          return;
        }

        // Buscar loja pelo CPF/CNPJ
        const apiUrl = getPrimaryApiRoot();
        const url = `${apiUrl}/api/superadmin/lojas/buscar-por-documento/?documento=${documentoLimpo}`;

        const response = await fetch(url);

        if (!response.ok) {
          if (response.status === 404) {
            setError('Nenhuma loja encontrada com este CPF/CNPJ');
          } else if (response.status === 429) {
            setError('Muitas tentativas agora. Aguarde um pouco e tente de novo.');
          } else {
            setError('Erro ao buscar loja. Tente novamente.');
          }
          setLoading(false);
          return;
        }

        const data = await response.json();
        const destino = data.atalho || data.slug;
        router.push(`/loja/${destino}/login`);
      }
      
    } catch (err) {
      setError('Erro ao conectar com o servidor. Tente novamente.');
      setLoading(false);
    }
  };

  const campo = "mt-2 w-full rounded-xl border border-cyan-300/30 bg-[#04183f] px-4 py-3 text-base text-white outline-none placeholder:text-slate-500 focus:border-sky-300";
  const aba = (ativa: boolean) =>
    `rounded-full px-4 py-2 text-sm font-semibold transition ${ativa ? "bg-[#2f6bff] text-white" : "text-slate-300 hover:text-white"}`;

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center bg-[#020817]/75 p-4 backdrop-blur-md"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="acesso-rapido-titulo"
        className="relative w-full max-w-md rounded-2xl border border-cyan-300/40 bg-[#071833] p-6 text-white shadow-[0_24px_80px_rgba(0,0,0,0.45)]"
        onClick={(evento) => evento.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute right-3 top-3 rounded-full p-2 text-slate-300 hover:bg-white/10 hover:text-white"
          aria-label="Fechar"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="mb-4 flex justify-center">
          <img src="/homepage/logo-mark.png" alt="" className="h-14 w-auto" />
        </div>

        <h2 id="acesso-rapido-titulo" className="text-center text-2xl font-bold tracking-tight">
          Acesso rápido
        </h2>
        <p className="mb-6 mt-2 text-center text-sm text-slate-300">
          {tipoAcesso === "documento"
            ? "Informe o CPF ou o CNPJ da empresa para entrar no sistema."
            : "Informe o atalho da empresa para entrar no sistema."}
        </p>

        <div className="mb-6 grid grid-cols-2 gap-1 rounded-full border border-white/10 bg-[#04183f] p-1">
          <button type="button" onClick={() => { setTipoAcesso("documento"); setError(""); }} className={aba(tipoAcesso === "documento")}>
            CPF/CNPJ
          </button>
          <button type="button" onClick={() => { setTipoAcesso("atalho"); setError(""); }} className={aba(tipoAcesso === "atalho")}>
            Atalho
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {tipoAcesso === "documento" ? (
            <div>
              <label htmlFor="documento" className="text-sm font-medium text-slate-200">
                CPF ou CNPJ
              </label>
              <input
                id="documento"
                type="text"
                value={documento}
                onChange={handleChange}
                placeholder="000.000.000-00 ou 00.000.000/0000-00"
                className={campo}
                disabled={loading}
                autoFocus
              />
            </div>
          ) : (
            <div>
              <label htmlFor="atalho" className="text-sm font-medium text-slate-200">
                Atalho da empresa
              </label>
              <input
                id="atalho"
                type="text"
                value={atalho}
                onChange={(e) => {
                  setAtalho(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""));
                  setError("");
                }}
                placeholder="minha-empresa"
                className={campo}
                disabled={loading}
                autoFocus
              />
            </div>
          )}
          {error && <p className="text-sm text-rose-300" role="alert">{error}</p>}

          <button
            type="submit"
            disabled={loading || (tipoAcesso === "documento" ? !documento : !atalho)}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-[#2f6bff] py-3 font-semibold text-white hover:bg-[#2457d6] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Buscando..." : (
              <>
                <LogIn className="h-5 w-5" />
                Acessar o sistema
              </>
            )}
          </button>
        </form>

        <p className="mt-6 border-t border-white/10 pt-5 text-center text-sm text-slate-300">
          Ainda não tem acesso?{" "}
          <a href="/cadastro" className="font-semibold text-sky-300 hover:text-white">
            Cadastre a empresa
          </a>
        </p>
      </div>
    </div>
  );
}
