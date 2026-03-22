'use client';

import { useEffect, useState } from 'react';

interface WhyUsBenefit {
  id: number;
  titulo: string;
  descricao?: string;
  icone?: string;
  ativo?: boolean;
}

export default function WhyUs() {
  const [benefits, setBenefits] = useState<WhyUsBenefit[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBenefits = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/homepage/`);
        const data = await response.json();
        
        if (data.whyus && data.whyus.length > 0) {
          setBenefits(data.whyus);
        } else {
          // Valores padrão se não houver dados
          setBenefits([
            { id: 1, titulo: "Aumente sua produtividade", icone: "✓" },
            { id: 2, titulo: "Organize seus clientes", icone: "✓" },
            { id: 3, titulo: "Controle suas vendas", icone: "✓" },
            { id: 4, titulo: "Sistema na Nuvem", icone: "✓" },
          ]);
        }
      } catch (error) {
        // Em caso de erro, usar valores padrão
        setBenefits([
          { id: 1, titulo: "Aumente sua produtividade", icone: "✓" },
          { id: 2, titulo: "Organize seus clientes", icone: "✓" },
          { id: 3, titulo: "Controle suas vendas", icone: "✓" },
          { id: 4, titulo: "Sistema na Nuvem", icone: "✓" },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchBenefits();
  }, []);

  if (loading) {
    return (
      <section id="beneficios" className="w-full py-12 sm:py-16 md:py-20 bg-gray-50">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-gray-500">Carregando...</div>
        </div>
      </section>
    );
  }

  return (
    <section id="beneficios" className="w-full py-12 sm:py-16 md:py-20 bg-gray-50">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-8 sm:mb-12 text-gray-900">
          Por que usar o LWKS Sistemas?
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {benefits.map((item) => (
            <div
              key={item.id}
              className="flex items-center gap-3 bg-white p-4 rounded-xl border border-gray-100"
            >
              <span className="flex-shrink-0 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm">
                {item.icone || '✓'}
              </span>
              <span className="text-sm sm:text-base font-medium text-gray-900">{item.titulo}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
