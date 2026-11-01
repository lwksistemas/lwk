export const BOTOES_HOME = {
  inicio: "Início",
  solucoes: "Soluções",
  segmentos: "Segmentos",
  planos: "Planos",
  contato: "Contato",
  acessar: "Acessar sistemas",
  fale: "Fale Conosco",
  conhecer_crm: "Conhecer o CRM",
  conhecer_clinica: "Conhecer o sistema",
  orcamento: "Solicitar orçamento",
  ver_planos: "Ver planos",
  proposta: "Solicitar proposta",
  orcamento_plano: "Pedir orçamento",
  enviar_form: "Solicitar demonstração",
  whatsapp_form: "Enviar pelo WhatsApp",
} as const;

export type ChaveBotao = keyof typeof BOTOES_HOME;

export const LEGENDA_BOTOES: { id: ChaveBotao; onde: string }[] = [
  { id: "inicio", onde: "Menu" },
  { id: "solucoes", onde: "Menu" },
  { id: "segmentos", onde: "Menu" },
  { id: "planos", onde: "Menu" },
  { id: "contato", onde: "Menu" },
  { id: "acessar", onde: "Menu" },
  { id: "fale", onde: "Menu, botão verde" },
  { id: "conhecer_crm", onde: "Cartão do CRM" },
  { id: "conhecer_clinica", onde: "Cartão da clínica" },
  { id: "orcamento", onde: "Sistemas personalizados" },
  { id: "ver_planos", onde: "Planos, clínica" },
  { id: "proposta", onde: "Planos, CRM" },
  { id: "orcamento_plano", onde: "Planos, personalizado" },
  { id: "enviar_form", onde: "Formulário de contato" },
  { id: "whatsapp_form", onde: "Formulário de contato" },
];

export function rotuloBotao(mapa: Record<string, string> | undefined, chave: ChaveBotao) {
  const valor = mapa?.[chave]?.trim();
  return valor || BOTOES_HOME[chave];
}
