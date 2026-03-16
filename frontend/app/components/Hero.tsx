import Link from "next/link";
import type { Hero as HeroType } from "@/types/homepage";

interface HeroProps {
  hero: HeroType | null;
}

export default function Hero({ hero }: HeroProps) {
  if (!hero) return null;

  return (
    <section className="bg-white py-24">
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-10 items-center px-4">
        <div>
          <h1 className="text-5xl font-bold mb-6 text-gray-900">
            {hero.titulo}
          </h1>
          <p className="text-lg text-gray-600 mb-8">{hero.subtitulo}</p>
          <Link
            href="/superadmin/login"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            {hero.botao_texto}
          </Link>
        </div>
        <div className="hidden md:block">
          <div className="rounded-lg shadow-xl bg-gradient-to-br from-blue-100 to-blue-200 aspect-video flex items-center justify-center">
            <svg
              className="w-32 h-32 text-blue-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
        </div>
      </div>
    </section>
  );
}
