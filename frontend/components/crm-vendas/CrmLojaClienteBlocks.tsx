'use client';

import type { LeadInfo } from '@/lib/crm-loja-types';

function formatEnderecoCliente(leadInfo: LeadInfo): string {
  const endereco = leadInfo.conta_info || leadInfo;
  const partes = [
    endereco.logradouro,
    endereco.numero ? `nº ${endereco.numero}` : '',
    endereco.complemento,
    endereco.bairro,
    endereco.cidade && endereco.uf ? `${endereco.cidade}/${endereco.uf}` : endereco.cidade || endereco.uf,
    endereco.cep ? `CEP ${endereco.cep}` : '',
  ].filter(Boolean);
  return partes.length > 0 ? partes.join(' - ') : '—';
}

function nomeClienteExibicao(leadInfo: LeadInfo): string {
  return (
    leadInfo.conta_info?.nome ||
    (leadInfo.cpf_cnpj?.replace(/\D/g, '').length === 11
      ? leadInfo.nome
      : leadInfo.empresa || leadInfo.nome)
  );
}

export function CrmClienteBlock({
  leadInfo,
  oportunidadeSelecionada = false,
  labelClass = 'block text-xs text-gray-500 dark:text-gray-400 mb-0.5',
  titleClass = 'text-sm font-medium text-gray-700 dark:text-gray-300',
  compact = false,
}: {
  leadInfo: LeadInfo | null;
  oportunidadeSelecionada?: boolean;
  labelClass?: string;
  titleClass?: string;
  compact?: boolean;
}) {
  const valueCls = compact ? '' : 'text-gray-800 dark:text-gray-200';
  const nameCls = compact ? 'font-medium' : 'font-medium text-gray-900 dark:text-white';

  return (
    <>
      <h3 className={titleClass}>Dados do Cliente</h3>
      {leadInfo ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div className="sm:col-span-2">
            <span className={labelClass}>Nome</span>
            <p className={nameCls}>{nomeClienteExibicao(leadInfo)}</p>
          </div>
          {leadInfo.conta_info?.razao_social && (
            <div className="sm:col-span-2">
              <span className={labelClass}>Razão Social</span>
              <p className={valueCls}>{leadInfo.conta_info.razao_social}</p>
            </div>
          )}
          {(leadInfo.conta_info?.cnpj || leadInfo.cpf_cnpj) && (
            <div>
              <span className={labelClass}>CNPJ</span>
              <p className={valueCls}>{leadInfo.conta_info?.cnpj || leadInfo.cpf_cnpj}</p>
            </div>
          )}
          {leadInfo.conta_info?.inscricao_estadual && (
            <div>
              <span className={labelClass}>Inscrição Estadual</span>
              <p className={valueCls}>{leadInfo.conta_info.inscricao_estadual}</p>
            </div>
          )}
          <div>
            <span className={labelClass}>Email</span>
            <p className={valueCls}>{leadInfo.conta_info?.email || leadInfo.email || '—'}</p>
          </div>
          <div>
            <span className={labelClass}>Telefone</span>
            <p className={valueCls}>{leadInfo.conta_info?.telefone || leadInfo.telefone || '—'}</p>
          </div>
          {leadInfo.conta_info?.site && (
            <div className="sm:col-span-2">
              <span className={labelClass}>Site</span>
              <p className={valueCls}>{leadInfo.conta_info.site}</p>
            </div>
          )}
          <div className="sm:col-span-2">
            <span className={labelClass}>Endereço</span>
            <p className={valueCls}>{formatEnderecoCliente(leadInfo)}</p>
          </div>
        </div>
      ) : oportunidadeSelecionada ? (
        <p className="text-xs text-gray-500">Carregando dados do cliente...</p>
      ) : (
        <p className="text-xs text-gray-500">Selecione uma oportunidade para ver os dados do cliente.</p>
      )}
    </>
  );
}
