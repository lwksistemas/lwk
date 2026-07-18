"use client";

import { Printer, Mail, MessageCircle } from "lucide-react";

interface ReceberReciboActionsProps {
  onImprimir: () => void;
  onEmail: () => void;
  onWhatsApp: () => void;
}

export function ReceberReciboActions({
  onImprimir,
  onEmail,
  onWhatsApp,
}: ReceberReciboActionsProps) {
  return (
    <div className="grid grid-cols-3 gap-3">
      <button
        type="button"
        onClick={onImprimir}
        className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
      >
        <Printer size={24} className="text-gray-700 dark:text-gray-300" />
        <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Imprimir</span>
      </button>
      <button
        type="button"
        onClick={onEmail}
        className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
      >
        <Mail size={24} className="text-gray-700 dark:text-gray-300" />
        <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Email</span>
      </button>
      <button
        type="button"
        onClick={onWhatsApp}
        className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
      >
        <MessageCircle size={24} className="text-gray-700 dark:text-gray-300" />
        <span className="text-xs font-medium text-gray-700 dark:text-gray-300">WhatsApp</span>
      </button>
    </div>
  );
}
