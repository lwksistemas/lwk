export default function DashboardPreview() {
  return (
    <section className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
          Dashboard Moderno
        </h2>
        <div className="rounded-xl overflow-hidden shadow-2xl border border-gray-200 bg-white">
          <div className="aspect-video bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-8">
            <div className="w-full max-w-2xl mx-auto">
              <div className="flex gap-4 mb-6">
                <div className="w-20 h-10 bg-blue-600 rounded-full" />
                <div className="flex-1 gap-2 flex">
                  {["Dashboard", "Clientes", "Vendas"].map((_, i) => (
                    <div
                      key={i}
                      className="h-8 w-24 bg-gray-200 rounded"
                    />
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-20 bg-white rounded-lg border border-gray-200 shadow-sm"
                  />
                ))}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="h-32 bg-white rounded-lg border border-gray-200 shadow-sm" />
                <div className="h-32 bg-white rounded-lg border border-gray-200 shadow-sm" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
