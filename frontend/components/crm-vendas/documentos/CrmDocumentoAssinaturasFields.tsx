'use client';

interface Props {
  nomeVendedor: string;
  nomeCliente: string;
  onNomeVendedorChange: (value: string) => void;
  onNomeClienteChange: (value: string) => void;
  inputCls: string;
  labelCls: string;
  vendedorPlaceholder?: string;
  clientePlaceholder?: string;
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
}: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <label className={labelCls}>Nome do Vendedor</label>
        <input
          type="text"
          value={nomeVendedor}
          onChange={(e) => onNomeVendedorChange(e.target.value)}
          className={inputCls}
          placeholder={vendedorPlaceholder || 'Nome do vendedor'}
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Nome que aparecerá na assinatura do PDF</p>
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
