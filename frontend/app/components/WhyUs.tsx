import { SectionContainer } from "@/components/shared/SectionContainer";
import type { WhyUsBenefit } from "@/types/homepage";

const DEFAULT_BENEFITS: WhyUsBenefit[] = [
  { id: 1, titulo: "Aumente sua produtividade", icone: "✓" },
  { id: 2, titulo: "Organize seus clientes", icone: "✓" },
  { id: 3, titulo: "Controle suas vendas", icone: "✓" },
  { id: 4, titulo: "Sistema na Nuvem", icone: "✓" },
];

interface WhyUsProps {
  whyus: WhyUsBenefit[];
}

export default function WhyUs({ whyus }: WhyUsProps) {
  const benefits = whyus.length > 0 ? whyus : DEFAULT_BENEFITS;

  return (
    <SectionContainer id="beneficios" className="bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 dark:from-gray-900 dark:via-gray-850 dark:to-gray-900">
      <h2 className="text-2xl sm:text-3xl font-bold text-center mb-8 sm:mb-12 text-gray-900 dark:text-white">
        Por que usar o LWK Sistemas?
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {benefits.map((item) => (
          <div
            key={item.id}
            className="flex items-center gap-3 bg-white dark:bg-gray-800 p-4 rounded-xl border border-green-100 dark:border-gray-700 shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5"
          >
            <span className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center text-white text-sm shadow-md">
              {item.icone || '✓'}
            </span>
            <span className="text-sm sm:text-base font-medium text-gray-900 dark:text-gray-100">{item.titulo}</span>
          </div>
        ))}
      </div>
    </SectionContainer>
  );
}
