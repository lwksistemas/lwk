import type { Funcionalidade } from "@/types/homepage";

interface FeaturesProps {
  funcionalidades: Funcionalidade[];
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

export default function Features({ funcionalidades }: FeaturesProps) {
  if (!funcionalidades?.length) return null;

  return (
    <section id="funcionalidades" className="py-20 bg-gray-50">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
          Funcionalidades
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {funcionalidades.map((f) => (
            <div
              key={f.id}
              className="bg-white p-6 rounded-xl shadow hover:shadow-lg transition-shadow"
            >
              <div className="mb-4">{renderIcon(f.icone)}</div>
              <h3 className="text-xl font-bold mb-2 text-gray-900">{f.titulo}</h3>
              <p className="text-gray-600">{f.descricao}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
