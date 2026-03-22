import Link from "next/link";
import { IconRenderer } from "@/components/shared/IconRenderer";
import { SectionContainer } from "@/components/shared/SectionContainer";
import { DEFAULT_MODULOS } from "@/lib/homepage-constants";
import type { Modulo } from "@/types/homepage";

interface ModulesProps {
  modulos: Modulo[];
}

export default function Modules({ modulos }: ModulesProps) {
  const items = modulos?.length
    ? modulos
    : DEFAULT_MODULOS.map((m, i) => ({ ...m, id: i }));

  return (
    <SectionContainer id="modulos" background="gray">
      <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
        Sistemas disponíveis
      </h2>
      <div className="grid md:grid-cols-3 gap-8">
        {items.map((m, idx) => {
          const content = (
            <div className="border border-gray-200 p-6 rounded-xl hover:border-blue-500 hover:shadow-lg transition-all h-full bg-white">
              <IconRenderer
                icone={m.icone}
                imagem={m.imagem}
                alt={m.nome}
                size="md"
              />
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
    </SectionContainer>
  );
}
