export const MENSAGEM_FALE_CONOSCO =
  "Olá! Acessei o site da LWK Sistemas e gostaria de conhecer melhor as soluções oferecidas.";

const PADROES_ANTIGOS = new Set([
  "",
  "Olá! Gostaria de saber mais sobre o LWK Sistemas.",
  "Olá! Conheci a LWK Sistemas pelo site e gostaria de falar com o comercial.",
]);

export function mensagemComercial(mensagem?: string | null) {
  const texto = (mensagem || "").trim();
  if (PADROES_ANTIGOS.has(texto)) return MENSAGEM_FALE_CONOSCO;
  return texto;
}

export function urlWhatsapp(telefone?: string | null, mensagem?: string | null) {
  const numero = (telefone || "").replace(/\D/g, "");
  if (!numero) return null;
  return `https://wa.me/${numero}?text=${encodeURIComponent(mensagemComercial(mensagem))}`;
}

const ALVO_DEMONSTRACAO: Record<string, string> = {
  "crm-vendas": "do LWK Sales Cloud — CRM de Vendas",
  "clinicas-estetica": "da Gestão para Clínicas de Estética",
  personalizados: "de um sistema personalizado",
  outros: "das soluções da LWK Sistemas",
};

export function mensagemDemonstracao(produto: string, nome: string, empresa: string) {
  const alvo = ALVO_DEMONSTRACAO[produto] || "das soluções da LWK Sistemas";
  let texto = `Olá! Gostaria de agendar uma demonstração ${alvo}.`;
  const pessoa = nome.trim();
  const negocio = empresa.trim();
  if (pessoa && negocio) texto += ` Meu nome é ${pessoa} e minha empresa é ${negocio}.`;
  else if (pessoa) texto += ` Meu nome é ${pessoa}.`;
  else if (negocio) texto += ` Minha empresa é ${negocio}.`;
  return texto;
}

export function mensagemContato(nome: string, empresa: string, mensagem: string) {
  let texto = MENSAGEM_FALE_CONOSCO;
  const pessoa = nome.trim();
  const negocio = empresa.trim();
  if (pessoa && negocio) texto += ` Meu nome é ${pessoa} e minha empresa é ${negocio}.`;
  else if (pessoa) texto += ` Meu nome é ${pessoa}.`;
  else if (negocio) texto += ` Minha empresa é ${negocio}.`;
  if (mensagem.trim()) texto += ` ${mensagem.trim()}`;
  return texto;
}

export function mensagemOrcamento(nome: string, empresa: string, segmento: string, descricao: string) {
  let texto = "Olá! Gostaria de solicitar um orçamento de um sistema personalizado.";
  const pessoa = nome.trim();
  const negocio = empresa.trim();
  if (pessoa && negocio) texto += ` Meu nome é ${pessoa} e minha empresa é ${negocio}.`;
  else if (pessoa) texto += ` Meu nome é ${pessoa}.`;
  else if (negocio) texto += ` Minha empresa é ${negocio}.`;
  if (segmento.trim()) texto += ` Segmento: ${segmento.trim()}.`;
  if (descricao.trim()) texto += ` ${descricao.trim()}`;
  return texto;
}
