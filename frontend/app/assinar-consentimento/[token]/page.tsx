"use client";

import { useParams } from "next/navigation";
import { AssinarConsentimentoPageContent } from "@/components/assinar-consentimento/AssinarConsentimentoPageContent";

export default function AssinarConsentimentoPage() {
  const params = useParams();
  return <AssinarConsentimentoPageContent tokenRaw={params.token as string} />;
}
