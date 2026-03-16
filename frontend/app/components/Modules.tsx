import Link from "next/link";
import type { Modulo } from "@/types/homepage";

interface ModulesProps {
  modulos: Modulo[];
}

const DEFAULT_MODULOS: Omit<Modulo, "id">[] = [
  { nome: "CRM Vendas", descricao: "Gestão de leads e vendas", slug: "crm-vendas", icone: "📊" },
  { nome: "Clínica Estética", descricao: "Agenda e prontuários", slug: "clinica-estetica", icone: "💆" },
  { nome: "E-commerce", descricao: "Loja virtual completa", slug: "ecommerce", icone: "🛒" },
];

function renderIcon(icone?: string) {
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

export default function Modules({ modulos }: ModulesProps) {
  const items = modulos?.length
    ? modulos
    : DEFAULT_MODULOS.map((m, i) => ({ ...m, id: i }));

  return (
    <section id="modulos" className="py-20 bg-gray-50">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
          Sistemas disponíveis
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {items.map((m, idx) => {
            const content = (
              <div className="border border-gray-200 p-6 rounded-xl hover:border-blue-500 hover:shadow-lg transition-all h-full bg-white">
                <div className="mb-4">{renderIcon(m.icone)}</div>
                <h3 className="text-xl font-bold mb-2 text-gray-900">{m.nome}</h3>
                <p className="text-gray-600">{m.descricao}</p>
                {m.slug && (
                  <span className="inline-block mt-4 text-blue-600 font-medium">
                    Acessar →
                  </span>
                )}
              </div>
            );

            if (m.slug) {
              return (
                <Link key={m.id ?? idx} href={`/loja/${m.slug}/login`}>
                  {content}
                </Link>
              );
            }
            return <div key={m.id ?? idx}>{content}</div>;
          })}
        </div>
      </div>
    </section>
  );
}
