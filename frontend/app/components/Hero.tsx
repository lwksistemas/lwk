import Link from "next/link";
import Image from "next/image";
import type { Hero as HeroType } from "@/types/homepage";

interface HeroProps {
  hero: HeroType | null;
}

export default function Hero({ hero }: HeroProps) {
  const titulo = hero?.titulo ?? "Controle total da sua empresa em um único sistema";
  const subtitulo =
    hero?.subtitulo ??
    "Gerencie clientes, vendas, financeiro e relatórios em um CRM moderno e fácil de usar.";
  const botaoTexto = hero?.botao_texto ?? "Testar Gratuitamente";
  const mostrarBotaoPrincipal = hero?.botao_principal_ativo !== false;
  const imagem = hero?.imagem;

  return (
    <section className="w-full min-w-full bg-gradient-to-br from-blue-100 via-blue-50 to-blue-100 py-16 md:py-24">
      <div className="w-full max-w-7xl mx-auto grid md:grid-cols-2 gap-12 items-center px-4 sm:px-6 lg:px-8">
        <div>
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-gray-900 leading-tight">
            {titulo}
          </h1>
          <p className="text-lg text-gray-600 mb-8">{subtitulo}</p>
          <div className="flex flex-wrap gap-4">
            {mostrarBotaoPrincipal && (
              <Link
                href="/superadmin/login"
                className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                {botaoTexto}
              </Link>
            )}
            <Link
              href="#funcionalidades"
              className="inline-block bg-white text-blue-600 border-2 border-blue-600 px-6 py-3 rounded-lg hover:bg-blue-50 transition-colors font-medium"
            >
              Ver Demonstração
            </Link>
          </div>
        </div>
        <div className="hidden md:block">
          <div className="rounded-xl shadow-2xl bg-white p-4 border border-gray-100 overflow-hidden">
            {imagem ? (
              <div className="aspect-video relative rounded-lg overflow-hidden">
                <Image
                  src={imagem}
                  alt={titulo}
                  fill
                  className="object-cover"
                  priority
                />
              </div>
            ) : (
              <div className="aspect-video bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center">
                <div className="text-center p-8">
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    {[40, 70, 55].map((h, i) => (
                      <div
                        key={i}
                        className="bg-blue-200/60 rounded"
                        style={{ height: `${h}px` }}
                      />
                    ))}
                  </div>
                  <div className="flex gap-2 justify-center">
                    <div className="w-16 h-16 rounded-full bg-blue-300/50" />
                    <div className="w-24 h-12 rounded bg-blue-200/50" />
                  </div>
                  <p className="text-blue-700 font-semibold mt-4 text-lg">Dashboard</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
