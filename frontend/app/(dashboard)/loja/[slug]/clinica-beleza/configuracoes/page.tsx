'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ChevronRight } from 'lucide-react';
import { lojaApi } from '@/lib/clinica-beleza-api/client-ops';
import { ClinicaBelezaPageContent } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';

export default function ClinicaBelezaConfiguracoesPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;
  const [temSimulacao, setTemSimulacao] = useState(false);

  useEffect(() => {
    let vivo = true;
    lojaApi
      .info()
      .then((info) => {
        if (vivo) setTemSimulacao(Boolean(info.tem_simulacao_estetica));
      })
      .catch(() => {
        if (vivo) setTemSimulacao(false);
      });
    return () => {
      vivo = false;
    };
  }, []);

  const opcoes = [
    {
      titulo: 'Pagar assinatura',
      descricao: 'Baixar boleto e ver o histórico de pagamentos.',
      href: `/loja/${slug}/assinatura`,
      itens: ['Baixar boleto', 'Histórico de pagamento'],
    },
    {
      titulo: 'Identidade visual',
      descricao: 'Cor do menu, fundo das páginas, cores dos status e as colunas de Atendimentos e Estoque.',
      href: `${base}/aparencia`,
      itens: ['Cor do menu', 'Fundo das páginas', 'Cores dos status na agenda', 'Colunas de Atendimentos', 'Colunas de Estoque'],
    },
    {
      titulo: 'Configurar tela de login',
      descricao: 'Logo, fundo e cores da tela de login da clínica.',
      href: `${base}/login`,
      itens: ['Logo', 'Imagem de fundo', 'Cores do login'],
    },
    {
      titulo: 'Contato no recibo',
      descricao: 'Telefone, e-mail, cor e logomarca do recibo impresso ou enviado ao paciente.',
      href: `${base}/contato`,
      itens: ['Telefone da clínica', 'E-mail da clínica', 'Cor do recibo', 'Logomarca do recibo'],
    },
    {
      titulo: 'Cadastrar profissionais',
      descricao: 'Equipe da clínica e acessos ao sistema.',
      href: `/loja/${slug}/clinica-beleza/profissionais`,
      itens: ['Adicionar profissionais', 'Perfis de acesso', 'Horários de trabalho'],
    },
    {
      titulo: 'Configurar WhatsApp',
      descricao: 'Confirmações e lembretes de agendamento por WhatsApp.',
      href: `/loja/${slug}/configuracoes/whatsapp`,
      itens: ['Integração WhatsApp', 'Lembretes de consultas'],
    },
    {
      titulo: 'Receituário Memed — Timbrado',
      descricao: 'PDF timbrado A4 para receitas e pedidos de exames.',
      href: `${base}/memed`,
      itens: ['Upload do PDF timbrado da clínica', 'Aplica aos prescritores desta loja', 'Receita e exames'],
    },
    ...(temSimulacao
      ? [
          {
            titulo: 'Simulação estética',
            descricao: 'Chave YouCam API desta clínica. Cada loja configura a própria conta.',
            href: `${base}/simulacao`,
            itens: ['Somente no plano Completo', 'Chave individual da clínica', 'Não compartilhada com outras lojas'],
          },
        ]
      : []),
    {
      titulo: 'Nota fiscal (NFS-e)',
      descricao: 'Provedor e certificado da nota de serviço.',
      href: `${base}/nota-fiscal`,
      itens: ['Provedor de NF', 'Certificado digital', 'Emissão do serviço'],
    },
    {
      titulo: 'Cupom fiscal (NFC-e)',
      descricao: 'Cupom das vendas de produto. O recibo continua.',
      href: `${base}/cupom-fiscal`,
      itens: ['Regime e CSC', 'Inscrição estadual', 'Homologação ou produção'],
    },
    {
      titulo: 'Backup',
      descricao: 'Exportar e importar uma cópia dos dados desta clínica.',
      href: `${base}/backup`,
      itens: ['Exportar backup', 'Importar backup', 'Restaurar dados'],
    },
  ];

  return (
    <>
      <ClinicaBelezaStandardPageHeader title="Configurações" showOffline={false} actionsOnly />
      <ClinicaBelezaPageContent>
        <h1 className="mb-1 text-2xl font-semibold text-gray-900 dark:text-gray-100 sm:text-3xl">Configurações</h1>
        <p className="mb-4 max-w-2xl text-sm text-[#8a6e74] dark:text-gray-400">
          Assinatura, login, aparência, equipe, recibo, nota, cupom e backup desta clínica.
        </p>
        <ul className="grid gap-3 md:grid-cols-2">
          {opcoes.map((op) => (
            <li key={op.href} className="overflow-hidden rounded-3xl border border-[#f0e4e6] bg-white dark:border-gray-700 dark:bg-gray-800">
              <Link href={op.href} className="flex h-full items-start justify-between gap-3 px-4 py-3 hover:bg-[#fbf6f4] dark:hover:bg-gray-700/40">
                <span className="min-w-0 text-left">
                  <span className="block font-medium text-gray-900 dark:text-gray-100">{op.titulo}</span>
                  <span className="mt-0.5 block text-sm text-[#8a6e74] dark:text-gray-400">{op.descricao}</span>
                  <span className="mt-1 block text-xs text-[#8a6e74] dark:text-gray-500">{op.itens.join(' · ')}</span>
                </span>
                <ChevronRight size={18} className="mt-1 shrink-0 text-[#8a6e74] dark:text-gray-400" />
              </Link>
            </li>
          ))}
        </ul>
      </ClinicaBelezaPageContent>
    </>
  );
}
