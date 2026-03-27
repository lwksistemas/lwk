/**
 * Fundo da página pública de cadastro.
 * Usa z-0 (nunca -z-10): índice negativo fica atrás do bg-white do <body> e some.
 */
export function CadastroFundo() {
  return (
    <>
      <div
        className="pointer-events-none fixed inset-0 z-0 dark:hidden"
        style={{
          backgroundColor: '#64748b',
          backgroundImage: `
            radial-gradient(ellipse 120% 90% at 50% -15%, rgba(99, 102, 241, 0.55), transparent 52%),
            radial-gradient(ellipse 90% 70% at 100% 30%, rgba(14, 165, 233, 0.4), transparent 48%),
            radial-gradient(ellipse 70% 60% at 0% 80%, rgba(167, 139, 250, 0.35), transparent 50%),
            linear-gradient(165deg, #64748b 0%, #94a3b8 28%, #cbd5e1 58%, #a5b4fc 100%)
          `,
        }}
        aria-hidden
      />
      <div
        className="pointer-events-none fixed inset-0 z-0 hidden bg-slate-950 dark:block"
        style={{
          backgroundImage: `
            radial-gradient(ellipse 100% 80% at 50% 0%, rgba(59, 130, 246, 0.28), transparent 55%),
            linear-gradient(180deg, rgb(15, 23, 42) 0%, rgb(30, 41, 59) 45%, rgb(15, 23, 42) 100%)
          `,
        }}
        aria-hidden
      />
    </>
  );
}
