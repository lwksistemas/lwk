"use client";

import { useParams } from "next/navigation";
import { AssinarConsentimentoPageContent } from "@/components/assinar-consentimento/AssinarConsentimentoPageContent";

export default function AssinarConsentimentoPage() {
  const params = useParams();
  const tokenRaw = params.token as string;
  return <AssinarConsentimentoPageContent tokenRaw={tokenRaw} />;
}
