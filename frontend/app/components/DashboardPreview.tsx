export default function DashboardPreview() {
  return (
    <section className="w-full py-12 sm:py-16 md:py-20 bg-white">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-8 sm:mb-12 text-gray-900">
          Dashboard Moderno
        </h2>
        <div className="rounded-xl overflow-hidden shadow-2xl border border-gray-200 bg-white">
          <div className="aspect-video bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4 sm:p-6 md:p-8">
            <div className="w-full max-w-2xl mx-auto">
              <div className="flex gap-2 sm:gap-4 mb-4 sm:mb-6">
                <div className="w-12 sm:w-20 h-8 sm:h-10 bg-blue-600 rounded-full" />
                <div className="flex-1 gap-1 sm:gap-2 flex overflow-x-auto">
                  {["Dashboard", "Clientes", "Vendas"].map((_, i) => (
                    <div
                      key={i}
                      className="h-6 sm:h-8 w-16 sm:w-24 bg-gray-200 rounded flex-shrink-0"
                    />
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-4 mb-2 sm:mb-4">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-16 sm:h-20 bg-white rounded-lg border border-gray-200 shadow-sm"
                  />
                ))}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4">
                <div className="h-24 sm:h-32 bg-white rounded-lg border border-gray-200 shadow-sm" />
                <div className="h-24 sm:h-32 bg-white rounded-lg border border-gray-200 shadow-sm" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
