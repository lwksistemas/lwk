import Link from "next/link";

export default function Header() {
  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto flex justify-between items-center p-4">
        <Link href="/" className="text-2xl font-bold text-blue-600">
          LWKS Sistemas
        </Link>
        <nav className="flex items-center gap-6">
          <a
            href="#funcionalidades"
            className="text-gray-600 hover:text-blue-600 transition-colors"
          >
            Funcionalidades
          </a>
          <a
            href="#modulos"
            className="text-gray-600 hover:text-blue-600 transition-colors"
          >
            Sistemas
          </a>
          <Link
            href="/superadmin/login"
            className="text-gray-600 hover:text-blue-600 transition-colors"
          >
            Login
          </Link>
        </nav>
      </div>
    </header>
  );
}
