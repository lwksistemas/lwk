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
      <h2 className="text-2xl sm:text-3xl font-bold text-center mb-8 sm:mb-12 text-gray-900">
        Funcionalidades do Sistema
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
        {items.map((f, i) => (
          <div
            key={f.id ?? i}
            className="bg-gradient-to-br from-blue-50 to-indigo-50 p-5 sm:p-6 rounded-xl border border-blue-100 hover:shadow-xl hover:border-blue-300 transition-all transform hover:-translate-y-1"
          >
            <IconRenderer
              icone={f.icone}
              imagem={f.imagem}
              alt={f.titulo}
              size="md"
            />
            <h3 className="text-lg sm:text-xl font-bold mb-2 text-gray-900">{f.titulo}</h3>
            <p className="text-sm sm:text-base text-gray-600">{f.descricao}</p>
          </div>
        ))}
      </div>
    </SectionContainer>
  );
}
