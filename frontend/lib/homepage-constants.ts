import type { Funcionalidade, Modulo } from '@/types/homepage';

// Mapa de ícones (sincronizado com IconRenderer)
export const ICON_MAP: Record<string, string> = {
  Users: "👥",
  BarChart: "📊",
  ShoppingCart: "🛒",
  DollarSign: "💰",
  Settings: "⚙️",
  Calendar: "📅",
  FileText: "📄",
  Package: "📦",
  TrendingUp: "📈",
  Heart: "❤️",
  Star: "⭐",
  Check: "✅",
};

// Funcionalidades padrão (fallback)
export const DEFAULT_FUNCIONALIDADES: Omit<Funcionalidade, "id">[] = [
  {
    titulo: "CRM de Clientes",
    descricao: "Gestão completa de contatos e leads",
    icone: "👥",
  },
  {
    titulo: "Gestão de Vendas",
    descricao: "Controle de oportunidades e pipeline",
    icone: "📊",
  },
  {
    titulo: "Relatórios Inteligentes",
    descricao: "Análises e métricas detalhadas em tempo real",
    icone: "📈",
  },
  {
    titulo: "Controle Financeiro",
    descricao: "Gestão de contas, faturamento e cobranças",
    icone: "💰",
  },
];

// Módulos padrão (fallback)
export const DEFAULT_MODULOS: Omit<Modulo, "id">[] = [
  {
    nome: "CRM Vendas",
    descricao: "Gestão completa de leads, oportunidades e vendas",
    slug: "crm-vendas",
    icone: "📊",
  },
  {
    nome: "Clínica Estética",
    descricao: "Agenda, prontuários e gestão de clientes",
    slug: "clinica-estetica",
    icone: "💆",
  },
  {
    nome: "E-commerce",
    descricao: "Loja virtual completa com gestão de produtos",
    slug: "ecommerce",
    icone: "🛒",
  },
];

// Estilos de botões CTA
export const CTA_BUTTON_STYLES = {
  primary: "inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium",
  secondary: "inline-block bg-white text-blue-600 border-2 border-blue-600 px-6 py-3 rounded-lg hover:bg-blue-50 transition-colors font-medium",
  large: "inline-block bg-blue-600 text-white px-10 py-4 rounded-lg hover:bg-blue-700 transition-colors font-semibold text-lg",
};

// Textos padrão
export const DEFAULT_TEXTS = {
  hero: {
    titulo: "Controle total da sua empresa em um único sistema",
    subtitulo: "Gerencie clientes, vendas, financeiro e relatórios em um CRM moderno e fácil de usar.",
    botao_texto: "Testar Gratuitamente",
  },
  cta: {
    titulo: "Pronto para começar?",
    botao_texto: "Criar Conta Grátis",
  },
};
