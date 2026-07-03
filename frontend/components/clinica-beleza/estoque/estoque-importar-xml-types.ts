export interface ProdutoPreview {
  nome: string;
  unidade_medida: string;
  quantidade: string;
  preco_custo: string;
  lote: string;
  validade: string | null;
}

export interface PreviewResult {
  preview: boolean;
  nota: { numero: string; fornecedor: string; data_emissao: string };
  produtos: ProdutoPreview[];
  total_produtos: number;
  aviso_destinatario?: string;
}

export interface ImportResult {
  criados: number;
  atualizados: number;
  erros: { nome: string; erros: Record<string, string[]> }[];
  nota: { numero: string; fornecedor: string; data_emissao: string };
  aviso_destinatario?: string;
}

export interface EstoqueImportarXmlModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}
