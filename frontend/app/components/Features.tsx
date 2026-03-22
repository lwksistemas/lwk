import Image from "next/image";
import type { Funcionalidade } from "@/types/homepage";

interface FeaturesProps {
  funcionalidades: Funcionalidade[];
}

const DEFAULT_FUNCIONALIDADES: Omit<Funcionalidade, "id">[] = [
  { titulo: "CRM de Clientes", descricao: "Gestão de contatos e leads", icone: "👥" },
  { titulo: "Gestão de Vendas", descricao: "Controle de oportunidades", icone: "📊" },
  { titulo: "Relatórios Inteligentes", descricao: "Análises e métricas detalhadas", icone: "📈" },
  { titulo: "Controle Financeiro", descricao: "Gestão de contas e faturamento", icone: "💰" },
];

function renderIcon(icone?: string, imagem?: string) {
  if (imagem) {
    return (
      <div className="relative w-16 h-16 mb-4">
        <Image
          src={imagem}
          alt="Ícone"
          fill
          className="object-contain"
        />
      </div>
    );
  }
  
  if (!icone || icone.length <= 2) {
    return <span className="text-4xl">{icone || "📦"}</span>;
  }
  const iconMap: Record<string, string> = {
    Users: "👥",
    BarChart: "📊",
    ShoppingCart: "🛒",
    DollarSign: "💰",
    Settings: "⚙️",
  };
  return <span className="text-4xl">{iconMap[icone] || "📦"}</span>;
}

export default function Features({ funcionalidades }: FeaturesProps) {
  const items = funcionalidades?.length
    ? funcionalidades
    : DEFAULT_FUNCIONALIDADES.map((f, i) => ({ ...f, id: i }));

  return (
    <section id="funcionalidades" className="w-full py-20 bg-white">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
          Funcionalidades do Sistema
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {items.map((f, i) => (
            <div
              key={f.id ?? i}
              className="bg-gray-50 p-6 rounded-xl border border-gray-100 hover:shadow-lg transition-shadow"
            >
              <div className="mb-4">{renderIcon(f.icone, f.imagem)}</div>
              <h3 className="text-xl font-bold mb-2 text-gray-900">{f.titulo}</h3>
              <p className="text-gray-600">{f.descricao}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
