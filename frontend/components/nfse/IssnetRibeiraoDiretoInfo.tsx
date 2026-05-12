/**
 * Texto alinhado entre CRM (nota fiscal da loja) e Superadmin (NFS-e assinaturas):
 * mesmo tipo de integração ISSNet Ribeirão Preto (direto).
 */
export function IssnetRibeiraoDiretoInfo({
  className = '',
  prestadorLabel = 'prestador da nota',
}: {
  className?: string
  /** Ex.: "sua loja" ou "LWK (prestador das assinaturas)" */
  prestadorLabel?: string
}) {
  return (
    <div
      className={`rounded-lg border border-sky-200 bg-sky-50/90 p-4 text-sm text-sky-950 dark:border-sky-800 dark:bg-sky-950/30 dark:text-sky-100 ${className}`}
    >
      <p className="font-semibold">ISSNet — Ribeirão Preto (direto)</p>
      <p className="mt-2 text-xs leading-relaxed">
        As <strong>opções de configuração</strong> são as <strong>mesmas</strong> para qualquer empresa que emita
        direto na prefeitura por este integrador: credenciais do webservice, certificado A1, tributação (regime
        especial, Simples Nacional, incentivador cultural), descrição padrão do serviço, alíquota ISS, série / último
        RPS (e lote, se usar), e homologação/teste quando aplicável.
      </p>
      <p className="mt-2 text-xs leading-relaxed">
        <strong>Entre empresas</strong> (outro CNPJ / outro cadastro na prefeitura), o que normalmente{' '}
        <strong>só muda</strong> de uma para outra neste fluxo são o <strong>Código do Serviço Municipal</strong> e o{' '}
        <strong>Código CNAE</strong>. Os demais campos são os <strong>mesmos tipos de opção</strong>; os valores
        (credenciais, certificado, inscrição municipal, série e último RPS, etc.) são sempre os do{' '}
        {prestadorLabel}.
      </p>
    </div>
  )
}
