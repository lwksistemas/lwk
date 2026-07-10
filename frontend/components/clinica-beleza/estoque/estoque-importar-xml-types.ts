import type { EstoqueCategoria } from "@/components/clinica-beleza/estoque/estoque-types";

export interface ProdutoPreview {
  nome: string;
  unidade_medida: string;
  quantidade: string;
  preco_custo: string;
  lote: string;
  validade: string | null;
  categoria?: string;
  categoria_id?: number | null;
  categoria_inferida?: string;
  categoria_motivo?: string;
  ncm?: string;
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
  categorias?: EstoqueCategoria[];
  defaultCategoriaSlug?: string;
}
