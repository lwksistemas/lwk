import { IconRenderer } from "@/components/shared/IconRenderer";
import { SectionContainer } from "@/components/shared/SectionContainer";
import { DEFAULT_FUNCIONALIDADES } from "@/lib/homepage-constants";
import type { Funcionalidade } from "@/types/homepage";

interface FeaturesProps {
  funcionalidades: Funcionalidade[];
}

export default function Features({ funcionalidades }: FeaturesProps) {
  const items = funcionalidades?.length
    ? funcionalidades
    : DEFAULT_FUNCIONALIDADES.map((f, i) => ({ ...f, id: i }));

  return (
    <SectionContainer id="funcionalidades" background="white">
      <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
        Funcionalidades do Sistema
      </h2>
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
        {items.map((f, i) => (
          <div
            key={f.id ?? i}
            className="bg-gray-50 p-6 rounded-xl border border-gray-100 hover:shadow-lg transition-shadow"
          >
            <IconRenderer
              icone={f.icone}
              imagem={f.imagem}
              alt={f.titulo}
              size="md"
            />
            <h3 className="text-xl font-bold mb-2 text-gray-900">{f.titulo}</h3>
            <p className="text-gray-600">{f.descricao}</p>
          </div>
        ))}
      </div>
    </SectionContainer>
  );
}
