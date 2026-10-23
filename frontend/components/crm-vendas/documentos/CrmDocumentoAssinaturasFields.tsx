'use client';

import { nomesParaAssinatura } from '@/lib/crm-assinatura-vendedor';

interface Props {
  nomeVendedor: string;
  nomeCliente: string;
  onNomeVendedorChange: (value: string) => void;
  onNomeClienteChange: (value: string) => void;
  inputCls: string;
  labelCls: string;
  vendedorPlaceholder?: string;
  clientePlaceholder?: string;
  vendedores?: Array<{ id?: number; nome?: string | null }>;
}

export default function CrmDocumentoAssinaturasFields({
  nomeVendedor,
  nomeCliente,
  onNomeVendedorChange,
  onNomeClienteChange,
  inputCls,
  labelCls,
  vendedorPlaceholder,
  clientePlaceholder,
  vendedores,
}: Props) {
  const nomes = vendedores ? nomesParaAssinatura(vendedores, nomeVendedor) : [];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <label className={labelCls}>Nome do Vendedor</label>
        {vendedores ? (
          <select
            value={nomeVendedor}
            onChange={(e) => onNomeVendedorChange(e.target.value)}
            className={inputCls}
            aria-label="Nome do Vendedor"
          >
            <option value="">Selecione o vendedor</option>
            {nomes.map((nome) => (
              <option key={nome} value={nome}>
                {nome}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            value={nomeVendedor}
            onChange={(e) => onNomeVendedorChange(e.target.value)}
            className={inputCls}
            placeholder={vendedorPlaceholder || 'Nome do vendedor'}
          />
        )}
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {vendedores
            ? 'Vem do vendedor da oportunidade. Troque por outro vendedor cadastrado se precisar.'
            : 'Nome que aparecerá na assinatura do PDF'}
        </p>
      </div>
      <div>
        <label className={labelCls}>Nome do Cliente</label>
        <input
          type="text"
          value={nomeCliente}
          onChange={(e) => onNomeClienteChange(e.target.value)}
          className={inputCls}
          placeholder={clientePlaceholder || 'Nome do cliente'}
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Nome que aparecerá na assinatura do PDF</p>
      </div>
    </div>
  );
}
