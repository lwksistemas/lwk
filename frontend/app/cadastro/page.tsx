'use client';

import { Suspense, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { formatApiErrorBody } from '@/lib/api-errors';
import { cepDigitosValidos, cpfCnpjValido, mensagemCpfCnpjInvalido } from '@/lib/format-br';
import { logger } from '@/lib/logger';
import { useLojaForm, type LojaCadastrada } from '@/hooks/useLojaForm';
import { CadastroFundo } from '@/components/cadastro/CadastroFundo';
import { FormularioCadastroLoja } from '@/components/cadastro/FormularioCadastroLoja';
import { SucessoCadastro } from '@/components/cadastro/SucessoCadastro';
import { applyTelefoneInternacionalPayload } from '@/lib/format-br';

function CadastroPublicoContent() {
  const [loading, setLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [createdLoja, setCreatedLoja] = useState<LojaCadastrada | null>(null);
  const searchParams = useSearchParams();

  const lojaForm = useLojaForm(false, {
    tipoSlug: searchParams.get('tipo'),
    planoSlug: searchParams.get('plano'),
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!cpfCnpjValido(lojaForm.formData.cpf_cnpj)) {
      alert(mensagemCpfCnpjInvalido(lojaForm.formData.cpf_cnpj) || 'CPF/CNPJ inválido.');
      return;
    }

    if (!cepDigitosValidos(lojaForm.formData.cep)) {
      alert('Informe um CEP válido com 8 dígitos antes de finalizar o cadastro.');
      return;
    }

    setLoading(true);

    try {
      const payload = applyTelefoneInternacionalPayload({
        ...lojaForm.formData,
        provedor_boleto_preferido: lojaForm.formData.provedor_boleto_preferido || 'asaas',
      }, ['owner_telefone']);

      const response = await apiClient.post('/superadmin/lojas/', payload);
      const loja = response.data;
      setCreatedLoja(loja);
      setShowSuccess(true);
    } catch (error) {
      logger.warn('Erro ao criar loja:', error);
      const formatted = formatApiErrorBody(error);
      alert(`❌ Erro ao criar cadastro:\n\n${formatted || 'Erro desconhecido ao criar cadastro'}`);
    } finally {
      setLoading(false);
    }
  };

  if (showSuccess && createdLoja) {
    return <SucessoCadastro loja={createdLoja} email={lojaForm.formData.owner_email} />;
  }

  return (
    <div className="relative isolate flex min-h-[100dvh] min-h-screen w-full flex-col overflow-x-hidden">
      <CadastroFundo />

      <div className="relative z-10 flex min-h-[100dvh] w-full flex-1 flex-col bg-white/97 dark:bg-slate-950/95">
        <header className="shrink-0 border-b border-white/10 bg-gradient-to-r from-slate-800 via-blue-800 to-indigo-800 px-4 py-4 text-white sm:px-6 sm:py-5 lg:px-10 xl:px-12">
          <Link
            href="/"
            className="mb-2 inline-block text-sm text-white/85 transition hover:text-white"
          >
            ← Voltar para home
          </Link>
          <h1 className="text-2xl font-bold leading-tight sm:text-3xl lg:text-4xl">
            Cadastro de Nova Empresa
          </h1>
          <p className="mt-1.5 text-sm text-slate-200 sm:text-base">
            Preencha os dados abaixo para começar a usar o sistema
          </p>
        </header>

        <FormularioCadastroLoja
          lojaForm={lojaForm}
          onSubmit={handleSubmit}
          loading={loading}
          mostrarSenha={false}
        />
      </div>
    </div>
  );
}

export default function CadastroPublicoPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-50" />}>
      <CadastroPublicoContent />
    </Suspense>
  );
}
