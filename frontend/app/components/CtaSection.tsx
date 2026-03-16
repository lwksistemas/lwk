import Link from "next/link";

export default function CtaSection() {
  return (
    <section className="w-full py-20 bg-white">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-3xl font-bold mb-6 text-gray-900">
          Pronto para começar?
        </h2>
        <Link
          href="/superadmin/login"
          className="inline-block bg-blue-600 text-white px-10 py-4 rounded-lg hover:bg-blue-700 transition-colors font-semibold text-lg"
        >
          Criar Conta Grátis
        </Link>
      </div>
    </section>
  );
}
