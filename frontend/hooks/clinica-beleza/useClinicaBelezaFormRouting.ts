"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

/** Navegação lista ↔ formulário via ?novo=1 e ?id=X (padrão Pacientes/Convênios). */
export function useClinicaBelezaFormRouting(explicitBasePath?: string) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const basePath = explicitBasePath || pathname;

  const isNovo = searchParams.get("novo") === "1";
  const editIdParam = searchParams.get("id");
  const isFormView = isNovo || Boolean(editIdParam);
  const editId = editIdParam ? Number(editIdParam) : null;

  const voltarLista = () => router.replace(basePath, { scroll: false });
  const abrirNovo = () => router.replace(`${basePath}?novo=1`, { scroll: false });
  const abrirEditar = (id: number) => router.replace(`${basePath}?id=${id}`, { scroll: false });

  return { basePath, isNovo, editId, editIdParam, isFormView, voltarLista, abrirNovo, abrirEditar };
}
