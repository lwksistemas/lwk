import { getHomepage, getPaginaSite } from "@/lib/api";
import type { HomepageData } from "@/types/homepage";

export interface PaginaConteudo {
  slug: string;
  titulo: string;
  resumo: string;
  corpo: string;
  itens: string;
  mensagem_whatsapp: string;
}

const VAZIO: HomepageData = {
  hero: null,
  hero_imagens: [],
  funcionalidades: [],
  modulos: [],
  whyus: [],
  empresa: null,
  menu: { solucoes: [], segmentos: [] },
};

const RESERVA: Record<string, PaginaConteudo> = {
  "crm-vendas": {
    slug: "crm-vendas",
    titulo: "LWK Sales Cloud — CRM de Vendas",
    resumo: "Organize leads, funil, propostas, contratos, comissões e relatórios comerciais em um só lugar.",
    corpo: "O CRM de Vendas acompanha o comercial do primeiro contato até o fechamento.",
    itens: "Leads\nFunil de vendas\nOportunidades\nPropostas\nContratos\nComissões\nRelatórios comerciais",
    mensagem_whatsapp: "Olá! Gostaria de agendar uma demonstração do LWK Sales Cloud — CRM de Vendas.",
  },
  "clinicas-estetica": {
    slug: "clinicas-estetica",
    titulo: "Gestão para Clínicas de Estética",
    resumo: "Agenda, clientes, procedimentos, protocolos, estoque, financeiro e relatórios da clínica.",
    corpo: "O sistema da clínica reúne a operação do dia.",
    itens: "Agenda\nClientes\nProcedimentos\nProtocolos\nEstoque\nFinanceiro\nRelatórios",
    mensagem_whatsapp: "Olá! Gostaria de agendar uma demonstração da Gestão para Clínicas de Estética.",
  },
  personalizados: {
    slug: "personalizados",
    titulo: "Sistemas personalizados",
    resumo: "Software sob medida para a operação da sua empresa.",
    corpo: "A LWK desenvolve a solução em cima da rotina real.",
    itens: "Levantamento do processo\nTelas e regras sob medida\nSuporte depois da entrega",
    mensagem_whatsapp: "Olá! Conheci a LWK Sistemas pelo site e gostaria de conversar sobre um sistema personalizado.",
  },
  segmentos: {
    slug: "segmentos",
    titulo: "Segmentos atendidos",
    resumo: "A LWK atende empresas de diferentes portes e áreas.",
    corpo: "Clínicas de estética e equipes comerciais já têm sistema próprio. Outros segmentos não têm sistema pronto: a LWK desenvolve o software conforme a operação.",
    itens: "Clínicas de estética\nEquipes comerciais\nProjetos para outros segmentos",
    mensagem_whatsapp: "Olá! Conheci a LWK Sistemas pelo site e gostaria de saber se atendem o meu segmento.",
  },
  planos: {
    slug: "planos",
    titulo: "Planos",
    resumo: "Valores e o que entra em cada módulo.",
    corpo: "Escolha o módulo para ver os planos. Se o valor ainda não estiver publicado, peça uma demonstração.",
    itens: "",
    mensagem_whatsapp: "Olá! Conheci a LWK Sistemas pelo site e gostaria de conhecer os planos.",
  },
  contato: {
    slug: "contato",
    titulo: "Contato",
    resumo: "Fale com a LWK pelo formulário, telefone ou WhatsApp.",
    corpo: "Conte o que a empresa precisa. Retornamos pelo WhatsApp informado.",
    itens: "",
    mensagem_whatsapp: "Olá! Conheci a LWK Sistemas pelo site e gostaria de falar com o comercial.",
  },
  demonstracao: {
    slug: "demonstracao",
    titulo: "Solicitar demonstração",
    resumo: "Escolha o produto e peça uma apresentação.",
    corpo: "Diga qual sistema interessa. A mensagem do WhatsApp já cita o produto escolhido.",
    itens: "",
    mensagem_whatsapp: "Olá! Conheci a LWK Sistemas pelo site e gostaria de agendar uma demonstração.",
  },
};

export async function carregarHome(): Promise<HomepageData> {
  try {
    return await getHomepage();
  } catch {
    return VAZIO;
  }
}

export async function carregarPagina(slug: string): Promise<PaginaConteudo> {
  try {
    return await getPaginaSite(slug);
  } catch {
    return RESERVA[slug] ?? {
      slug,
      titulo: "LWK Sistemas",
      resumo: "",
      corpo: "",
      itens: "",
      mensagem_whatsapp: RESERVA.demonstracao.mensagem_whatsapp,
    };
  }
}

export function linkWhatsapp(telefone: string | undefined, mensagem: string) {
  const numero = (telefone || "").replace(/\D/g, "");
  if (!numero) return null;
  return `https://wa.me/${numero}${mensagem ? `?text=${encodeURIComponent(mensagem)}` : ""}`;
}
