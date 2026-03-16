import Link from "next/link";

export default function Header() {
  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto flex justify-between items-center p-4">
        <Link href="/" className="text-2xl font-bold text-blue-600">
          LWKS SISTEMAS
        </Link>
        <nav className="flex items-center gap-6">
          <a
            href="#funcionalidades"
            className="text-gray-600 hover:text-blue-600 transition-colors"
          >
            Funcionalidades
          </a>
          <a
            href="#beneficios"
            className="text-gray-600 hover:text-blue-600 transition-colors"
          >
            Benefícios
          </a>
          <a
            href="#modulos"
            className="text-gray-600 hover:text-blue-600 transition-colors"
          >
            Preços
          </a>
          <Link
            href="/superadmin/login"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Login
          </Link>
        </nav>
      </div>
    </header>
  );
}
