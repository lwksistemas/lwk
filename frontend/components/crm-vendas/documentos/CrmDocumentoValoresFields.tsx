'use client';

import {
  formatarValorComDesconto,
  type CrmDescontoTipo,
} from '@/lib/crm-documento-valores';

interface Props {
  valorTotal: string;
  descontoTipo: CrmDescontoTipo | string;
  descontoValor: string;
  onValorTotalChange: (value: string) => void;
  onDescontoTipoChange: (tipo: CrmDescontoTipo) => void;
  onDescontoValorChange: (value: string) => void;
  inputCls: string;
  labelCls: string;
  layout?: 'grid' | 'compact';
  valorInputClassName?: string;
  sectionClassName?: string;
}

function DescontoFields({
  descontoTipo,
  descontoValor,
  onDescontoTipoChange,
  onDescontoValorChange,
  inputCls,
  labelCls,
  layout,
}: Pick<
  Props,
  | 'descontoTipo'
  | 'descontoValor'
  | 'onDescontoTipoChange'
  | 'onDescontoValorChange'
  | 'inputCls'
  | 'labelCls'
  | 'layout'
>) {
  const isCompact = layout === 'compact';
  return (
    <div>
      <label className={labelCls}>Desconto</label>
      <div className={`flex gap-2 ${isCompact ? 'items-end' : ''}`}>
        <select
          value={descontoTipo || 'percentual'}
          onChange={(e) => onDescontoTipoChange(e.target.value as CrmDescontoTipo)}
          className={`${inputCls} ${isCompact ? 'max-w-[160px]' : 'max-w-[120px]'}`}
        >
          {isCompact ? (
            <>
              <option value="percentual">Percentual (%)</option>
              <option value="valor">Valor fixo (R$)</option>
            </>
          ) : (
            <>
              <option value="percentual">%</option>
              <option value="valor">R$</option>
            </>
          )}
        </select>
        <input
          type="number"
          min="0"
          step="0.01"
          max={descontoTipo === 'percentual' ? '100' : undefined}
          value={descontoValor || ''}
          onChange={(e) => onDescontoValorChange(e.target.value)}
          className={`${inputCls} ${isCompact ? 'max-w-[160px]' : ''}`}
          placeholder={descontoTipo === 'percentual' ? '0%' : '0,00'}
        />
      </div>
    </div>
  );
}

export default function CrmDocumentoValoresFields({
  valorTotal,
  descontoTipo,
  descontoValor,
  onValorTotalChange,
  onDescontoTipoChange,
  onDescontoValorChange,
  inputCls,
  labelCls,
  layout = 'grid',
  valorInputClassName,
  sectionClassName,
}: Props) {
  const showPreview =
    valorTotal && descontoValor && parseFloat(descontoValor) > 0;

  const preview = showPreview ? (
    <p className={`text-xs text-green-600 dark:text-green-400 ${layout === 'grid' ? 'sm:col-span-2' : 'mt-1'}`}>
      Valor com desconto: {formatarValorComDesconto(valorTotal, descontoTipo, descontoValor)}
    </p>
  ) : null;

  if (layout === 'grid') {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className={labelCls}>Valor total (R$)</label>
          <input
            type="number"
            min="0"
            step="0.01"
            value={valorTotal}
            onChange={(e) => onValorTotalChange(e.target.value)}
            className={inputCls}
            placeholder="0,00"
          />
        </div>
        <DescontoFields
          descontoTipo={descontoTipo}
          descontoValor={descontoValor}
          onDescontoTipoChange={onDescontoTipoChange}
          onDescontoValorChange={onDescontoValorChange}
          inputCls={inputCls}
          labelCls={labelCls}
          layout={layout}
        />
        {preview}
      </div>
    );
  }

  return (
    <>
      <div className={sectionClassName}>
        <label className={labelCls}>Valor total (R$)</label>
        <input
          type="number"
          min="0"
          step="0.01"
          value={valorTotal}
          onChange={(e) => onValorTotalChange(e.target.value)}
          className={`${inputCls} ${valorInputClassName || ''}`}
          placeholder="0,00"
        />
      </div>
      <div className={sectionClassName}>
        <DescontoFields
          descontoTipo={descontoTipo}
          descontoValor={descontoValor}
          onDescontoTipoChange={onDescontoTipoChange}
          onDescontoValorChange={onDescontoValorChange}
          inputCls={inputCls}
          labelCls={labelCls}
          layout={layout}
        />
        {preview}
      </div>
    </>
  );
}
