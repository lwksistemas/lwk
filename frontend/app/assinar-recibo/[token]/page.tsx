"use client";

import { useParams } from "next/navigation";
import { AssinarReciboPageContent } from "@/components/assinar-recibo/AssinarReciboPageContent";

export default function AssinarReciboPage() {
  const params = useParams();
  return <AssinarReciboPageContent tokenRaw={params.token as string} />;
}
