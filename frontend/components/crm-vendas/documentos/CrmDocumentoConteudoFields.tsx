'use client';

export interface CrmDocumentoTemplateOption {
  id: number;
  nome: string;
  conteudo: string;
  is_padrao: boolean;
}

interface Props {
  conteudo: string;
  onConteudoChange: (value: string) => void;
  inputCls: string;
  labelCls: string;
  placeholder?: string;
  templates?: CrmDocumentoTemplateOption[];
  onSelecionarTemplate?: (conteudo: string, nomeTemplate?: string) => void;
  onSalvarComoPadrao?: (conteudo: string) => void;
  salvandoPadrao?: boolean;
  salvarPadraoLabel?: string;
  minHeightClass?: string;
  rows?: number;
  showTemplateHint?: boolean;
  sectionClassName?: string;
  wrapTemplateAndContent?: boolean;
}

export default function CrmDocumentoConteudoFields({
  conteudo,
  onConteudoChange,
  inputCls,
  labelCls,
  placeholder = 'Descrição detalhada do documento...',
  templates = [],
  onSelecionarTemplate,
  onSalvarComoPadrao,
  salvandoPadrao = false,
  salvarPadraoLabel = 'Salvar como Proposta PADRAO',
  minHeightClass = 'min-h-[200px] lg:min-h-[240px]',
  rows = 10,
  showTemplateHint = false,
  sectionClassName,
  wrapTemplateAndContent = false,
}: Props) {
  const templateSelect =
    templates.length > 0 && onSelecionarTemplate ? (
      <div className={sectionClassName}>
        <label className={labelCls}>Usar template</label>
        <select
          onChange={(e) => {
            const template = templates.find((t) => String(t.id) === e.target.value);
            if (template) onSelecionarTemplate(template.conteudo, template.nome);
            e.target.value = '';
          }}
          className={inputCls}
          defaultValue=""
        >
          <option value="">Selecione um template (opcional)</option>
          {templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.nome} {t.is_padrao ? '(PADRÃO)' : ''}
            </option>
          ))}
        </select>
        {showTemplateHint && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Selecione um template para preencher o conteúdo automaticamente
          </p>
        )}
      </div>
    ) : null;

  const contentField = (
    <div className={wrapTemplateAndContent ? undefined : sectionClassName}>
      <div className="flex items-center justify-between gap-2 mb-1">
        <label className={labelCls}>Conteúdo</label>
        {onSalvarComoPadrao && conteudo.trim() && (
          <button
            type="button"
            onClick={() => onSalvarComoPadrao(conteudo)}
            disabled={salvandoPadrao}
            className="text-xs text-[#0176d3] hover:underline disabled:opacity-50"
          >
            {salvandoPadrao ? 'Salvando...' : salvarPadraoLabel}
          </button>
        )}
      </div>
      <textarea
        value={conteudo}
        onChange={(e) => onConteudoChange(e.target.value)}
        className={`${inputCls} ${minHeightClass} resize-y`}
        rows={rows}
        placeholder={placeholder}
      />
    </div>
  );

  if (wrapTemplateAndContent) {
    return (
      <>
        {templateSelect}
        {contentField}
      </>
    );
  }

  return (
    <>
      {templateSelect}
      {contentField}
    </>
  );
}
