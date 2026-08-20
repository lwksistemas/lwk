export const TERMO_TIPO_OPTIONS = [
  { value: "simples", label: "Termo simples" },
  { value: "interativo", label: "TCLE Interativo" },
] as const;

export const TERMO_SECAO_TIPO_OPTIONS = [
  { value: "sim_nao", label: "Leitura + SIM/NÃO + dúvidas" },
  { value: "assinatura", label: "Somente ciência" },
  { value: "gravidez", label: "Risco de gravidez" },
  { value: "fotos", label: "Fotos, som e imagem" },
  { value: "consinto", label: "Consentimento ou recusa" },
  { value: "profissional", label: "Declaração do profissional" },
] as const;

export function novaSecao() {
  return {
    id: crypto.randomUUID(),
    codigo: "",
    titulo: "",
    texto: "",
    tipo: "sim_nao" as const,
  };
}

export function buildTermoNovoPath(slug: string, id?: number) {
  const base = `/loja/${slug}/clinica-beleza/termos-consentimento/novo`;
  return id ? `${base}?id=${id}` : base;
}

export function buildTermoListaPath(slug: string) {
  return `/loja/${slug}/clinica-beleza/termos-consentimento`;
}
