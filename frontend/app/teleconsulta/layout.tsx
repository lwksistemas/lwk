import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Teleconsulta',
  robots: 'noindex, nofollow',
};

export default function TeleconsultaLayout({ children }: { children: React.ReactNode }) {
  return <div className="min-h-[100dvh] w-full bg-slate-100">{children}</div>;
}
