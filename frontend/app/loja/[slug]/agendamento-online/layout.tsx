import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Agendamento Online",
  description: "Agende seu atendimento de forma prática, rápida e segura.",
  manifest: undefined,
};

export default function AgendamentoOnlineLayout({ children }: { children: React.ReactNode }) {
  return children;
}
