import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Confirmar agendamento',
  robots: 'noindex, nofollow',
};

export default function ConfirmarAgendamentoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-[100dvh] w-full bg-neutral-100 md:bg-neutral-900/75 md:backdrop-blur-sm">
      {children}
    </div>
  );
}
