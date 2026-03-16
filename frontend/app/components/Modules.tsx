import Link from "next/link";
import type { Modulo } from "@/types/homepage";

interface ModulesProps {
  modulos: Modulo[];
}

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
  if (!modulos?.length) return null;

  return (
    <section id="modulos" className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
          Sistemas disponíveis
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {modulos.map((m) => {
            const content = (
              <div className="border border-gray-200 p-6 rounded-xl hover:border-blue-500 hover:shadow-lg transition-all h-full">
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
                <Link key={m.id} href={`/loja/${m.slug}/login`}>
                  {content}
                </Link>
              );
            }
            return <div key={m.id}>{content}</div>;
          })}
        </div>
      </div>
    </section>
  );
}
