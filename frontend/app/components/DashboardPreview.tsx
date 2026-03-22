export default function DashboardPreview() {
  return (
    <section className="w-full py-12 sm:py-16 md:py-20 bg-white">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-8 sm:mb-12 text-gray-900">
          Dashboard Moderno
        </h2>
        <div className="rounded-xl overflow-hidden shadow-2xl border border-gray-200 bg-white">
          <div className="aspect-video bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4 sm:p-6 md:p-8">
            <div className="w-full max-w-4xl mx-auto">
              {/* Header com logo e menu */}
              <div className="flex gap-2 sm:gap-4 mb-4 sm:mb-6">
                <div className="w-12 sm:w-20 h-8 sm:h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white text-xs sm:text-sm font-bold">LWK</span>
                </div>
                <div className="flex-1 gap-1 sm:gap-2 flex overflow-x-auto">
                  {["Dashboard", "Clientes", "Vendas", "Relatórios"].map((label, i) => (
                    <div
                      key={i}
                      className="h-6 sm:h-8 px-2 sm:px-4 bg-gray-200 rounded flex-shrink-0 flex items-center justify-center"
                    >
                      <span className="text-[10px] sm:text-xs text-gray-700 font-medium whitespace-nowrap">{label}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Cards de métricas */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-4 mb-2 sm:mb-4">
                {[
                  { label: "Vendas Hoje", value: "R$ 12.450", icon: "💰" },
                  { label: "Novos Clientes", value: "24", icon: "👥" },
                  { label: "Pedidos", value: "156", icon: "📦" }
                ].map((card, i) => (
                  <div
                    key={i}
                    className="h-20 sm:h-24 bg-white rounded-lg border border-gray-200 shadow-sm p-3 sm:p-4 flex flex-col justify-between"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs sm:text-sm text-gray-600">{card.label}</span>
                      <span className="text-lg sm:text-xl">{card.icon}</span>
                    </div>
                    <span className="text-lg sm:text-2xl font-bold text-gray-900">{card.value}</span>
                  </div>
                ))}
              </div>
              
              {/* Gráficos */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4">
                <div className="h-32 sm:h-40 bg-white rounded-lg border border-gray-200 shadow-sm p-3 sm:p-4">
                  <div className="text-xs sm:text-sm font-semibold text-gray-700 mb-2">Vendas do Mês</div>
                  <div className="flex items-end justify-between h-20 sm:h-24 gap-1">
                    {[40, 65, 45, 80, 55, 70, 90].map((height, i) => (
                      <div
                        key={i}
                        className="flex-1 bg-blue-500 rounded-t"
                        style={{ height: `${height}%` }}
                      />
                    ))}
                  </div>
                </div>
                <div className="h-32 sm:h-40 bg-white rounded-lg border border-gray-200 shadow-sm p-3 sm:p-4">
                  <div className="text-xs sm:text-sm font-semibold text-gray-700 mb-2">Produtos Mais Vendidos</div>
                  <div className="space-y-2">
                    {[85, 70, 55].map((width, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className="w-16 sm:w-20 text-[10px] sm:text-xs text-gray-600">Produto {i + 1}</div>
                        <div className="flex-1 bg-gray-200 rounded-full h-3 sm:h-4">
                          <div
                            className="bg-green-500 h-full rounded-full"
                            style={{ width: `${width}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
