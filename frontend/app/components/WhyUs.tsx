export default function WhyUs() {
  const benefits = [
    "Aumente sua produtividade",
    "Organize seus clientes",
    "Controle suas vendas",
    "Sistema na Nuvem",
  ];

  return (
    <section id="beneficios" className="py-20 bg-gray-50">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
          Por que usar o LWKS Sistemas?
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {benefits.map((item, i) => (
            <div
              key={i}
              className="flex items-center gap-3 bg-white p-4 rounded-xl border border-gray-100"
            >
              <span className="flex-shrink-0 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white">
                ✓
              </span>
              <span className="font-medium text-gray-900">{item}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
