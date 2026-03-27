'use client';

import { useState } from 'react';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { useLojaForm } from '@/hooks/useLojaForm';
import { CadastroFundo } from '@/components/cadastro/CadastroFundo';
import { FormularioCadastroLoja } from '@/components/cadastro/FormularioCadastroLoja';
import { SucessoCadastro } from '@/components/cadastro/SucessoCadastro';

export default function CadastroPublicoPage() {
  const [loading, setLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [createdLoja, setCreatedLoja] = useState<any>(null);
  
  // Hook customizado sem campo de senha (gerada automaticamente no backend)
  const lojaForm = useLojaForm(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        ...lojaForm.formData,
        provedor_boleto_preferido: lojaForm.formData.provedor_boleto_preferido || 'asaas',
      };
      
      const response = await apiClient.post('/superadmin/lojas/', payload);
      const loja = response.data;
      setCreatedLoja(loja);
      setShowSuccess(true);
    } catch (error: any) {
      console.error('Erro ao criar loja:', error);
      
      let mensagemErro = '❌ Erro ao criar cadastro:\n\n';
      
      if (error.response?.data) {
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
        mensagemErro += 'Erro desconhecido ao criar cadastro';
      }
      
      alert(mensagemErro);
    } finally {
      setLoading(false);
    }
  };

  if (showSuccess && createdLoja) {
    return <SucessoCadastro loja={createdLoja} email={lojaForm.formData.owner_email} />;
  }

  return (
    <div className="relative isolate min-h-[100dvh] min-h-screen overflow-x-hidden">
      <CadastroFundo />

      <div className="relative z-10 mx-auto max-w-4xl px-3 pb-10 pt-4 sm:px-4 sm:pb-12 sm:pt-6 md:px-6 md:pt-8">
        <div className="overflow-hidden rounded-xl border border-slate-200/80 bg-white/95 shadow-xl shadow-slate-900/10 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-900/90 sm:rounded-2xl sm:shadow-2xl">
          {/* Header */}
          <div className="bg-gradient-to-r from-slate-800 via-blue-800 to-indigo-800 px-4 py-5 text-white sm:px-6 sm:py-6 md:px-8">
            <Link
              href="/"
              className="mb-2 inline-block text-sm text-white/85 transition hover:text-white"
            >
              ← Voltar para home
            </Link>
            <h1 className="text-2xl font-bold leading-tight sm:text-3xl md:text-4xl">
              Cadastro de Nova Empresa
            </h1>
            <p className="mt-2 text-sm text-slate-200 sm:text-base">
              Preencha os dados abaixo para começar a usar o sistema
            </p>
          </div>

          <FormularioCadastroLoja
            lojaForm={lojaForm}
            onSubmit={handleSubmit}
            loading={loading}
            mostrarSenha={false}
          />
        </div>
      </div>
    </div>
  );
}
