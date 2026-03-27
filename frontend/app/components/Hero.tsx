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
    <section className="w-full min-w-full bg-gradient-to-br from-blue-600 via-blue-500 to-indigo-600 py-12 sm:py-16 md:py-24 relative overflow-hidden">
      {/* Decoração de fundo */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDE0YzMuMzEgMCA2LTIuNjkgNi02cy0yLjY5LTYtNi02LTYgMi42OS02IDYgMi42OSA2IDYgNnptMC0xMGMyLjIxIDAgNCAxLjc5IDQgNHMtMS43OSA0LTQgNC00LTEuNzktNC00IDEuNzktNCA0LTR6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-20"></div>
      <div className="w-full max-w-7xl mx-auto grid md:grid-cols-2 gap-8 md:gap-12 items-center px-4 sm:px-6 lg:px-8 relative z-10">
        <div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 sm:mb-6 text-white leading-tight drop-shadow-lg">
            {titulo}
          </h1>
          <p className="text-base sm:text-lg text-blue-50 mb-6 sm:mb-8 drop-shadow">{subtitulo}</p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
            {mostrarBotaoPrincipal && (
              <Link
                href="/superadmin/login"
                className="inline-block text-center bg-white text-blue-600 px-6 py-3 rounded-lg hover:bg-blue-50 transition-all font-medium shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                {botaoTexto}
              </Link>
            )}
            <Link
              href="/cadastro"
              className="inline-block text-center bg-blue-700/50 backdrop-blur-sm text-white border-2 border-white/30 px-6 py-3 rounded-lg hover:bg-blue-700/70 transition-all font-medium shadow-lg"
            >
              Fazer Cadastro
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
