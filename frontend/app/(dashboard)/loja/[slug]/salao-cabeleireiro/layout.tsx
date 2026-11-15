"use client";

import { SalaoShell } from "@/components/salao/SalaoShell";

export default function SalaoLayout({ children }: { children: React.ReactNode }) {
  return <SalaoShell>{children}</SalaoShell>;
}
