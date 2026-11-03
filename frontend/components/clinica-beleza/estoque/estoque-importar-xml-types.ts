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
  nota: {
    numero: string;
    fornecedor: string;
    data_emissao: string;
    valor_total?: string | number | null;
  };
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

export interface NotaPendente {
  id: number;
  chave: string;
  numero: string;
  fornecedor: string;
  data_emissao: string;
  status: "resumo" | "pendente" | "importada" | "ignorada";
  status_display: string;
  origem: string;
  tem_xml: boolean;
  ultimo_erro: string;
}

export interface EstoqueImportarXmlModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  categorias?: EstoqueCategoria[];
  defaultCategoriaSlug?: string;
}
