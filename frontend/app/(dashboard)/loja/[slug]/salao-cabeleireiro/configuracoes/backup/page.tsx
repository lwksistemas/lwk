"use client";

import { useParams } from "next/navigation";
import { LojaBackupStandardContent } from "@/components/loja/LojaBackupStandardContent";
import { useLojaInfoPublica } from "@/hooks/useLojaInfoPublica";

export default function BackupSalaoPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const base = `/loja/${slug}/salao-cabeleireiro/configuracoes`;
  const { loja, loading, error } = useLojaInfoPublica(slug);

  if (loading) return <p className="text-sm text-[#8a6e74]">Carregando...</p>;
  if (!loja || error) return <p className="text-sm text-red-700">Não foi possível carregar o salão.</p>;

  return (
    <LojaBackupStandardContent
      loja={loja}
      backHref={base}
      subtitle="Exporte os dados deste salão. A importação continua fechada."
      showImport={false}
      accentColor="#7A3044"
      warningItems={[
        "O backup inclui clientes, agenda, serviços, profissionais e caixa",
        "Recomendamos uma cópia antes de mudanças grandes",
      ]}
      exportBullets={["Clientes e profissionais", "Agenda e serviços", "Recebimentos do caixa"]}
    />
  );
}
