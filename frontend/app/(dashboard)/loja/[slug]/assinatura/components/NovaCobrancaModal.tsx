'use client';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CreditCard, Copy } from 'lucide-react';
import Image from 'next/image';
import { formatDate, formatCurrency } from '@/lib/financeiro-helpers';

interface NovaCobrancaData {
  boleto_url?: string;
  pix_qr_code?: string;
  pix_copy_paste?: string;
  due_date?: string;
  value?: number;
}

interface Props {
  data: NovaCobrancaData;
  onClose: () => void;
  onCopiarPix: () => void;
}

export function NovaCobrancaModal({ data, onClose, onCopiarPix }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="bg-purple-900 text-white px-6 py-4">
          <h2 className="text-xl font-bold">Nova Cobrança Gerada</h2>
        </div>
        <div className="p-6 space-y-4">
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <p className="text-green-900 dark:text-green-100 font-medium">✅ Cobrança gerada com sucesso!</p>
            {data.due_date && <p className="text-sm text-green-800 dark:text-green-200 mt-1">Vencimento: {formatDate(data.due_date)}</p>}
            {data.value && <p className="text-sm text-green-800 dark:text-green-200">Valor: {formatCurrency(data.value)}</p>}
          </div>

          <Tabs defaultValue={data.boleto_url ? 'boleto' : 'pix'}>
            <TabsList className="w-full dark:bg-neutral-700">
              {data.boleto_url && <TabsTrigger value="boleto" className="flex-1">Boleto</TabsTrigger>}
              {data.pix_qr_code && <TabsTrigger value="pix" className="flex-1">PIX</TabsTrigger>}
            </TabsList>
            {data.boleto_url && (
              <TabsContent value="boleto" className="space-y-4 pt-4">
                <Button variant="outline" className="w-full" onClick={() => window.open(data.boleto_url, '_blank')}>
                  <CreditCard className="w-4 h-4 mr-2" /> Abrir Boleto
                </Button>
              </TabsContent>
            )}
            {data.pix_qr_code && (
              <TabsContent value="pix" className="space-y-4 pt-4">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div className="text-center">
                    <h4 className="font-medium mb-2 dark:text-gray-200">QR Code PIX</h4>
                    <div className="bg-white dark:bg-neutral-700 p-4 rounded border dark:border-neutral-600 inline-block">
                      <Image src={`data:image/png;base64,${data.pix_qr_code}`} alt="QR Code PIX" width={192} height={192} className="w-32 h-32 sm:w-48 sm:h-48" unoptimized />
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2 dark:text-gray-200">Código PIX</h4>
                    <div className="bg-muted dark:bg-neutral-700 p-3 rounded text-sm font-mono break-all dark:text-gray-200 max-h-32 overflow-y-auto">{data.pix_copy_paste || '—'}</div>
                    {data.pix_copy_paste && (
                      <Button variant="outline" className="mt-2 w-full" onClick={onCopiarPix}>
                        <Copy className="w-4 h-4 mr-2" /> Copiar código
                      </Button>
                    )}
                  </div>
                </div>
              </TabsContent>
            )}
          </Tabs>
        </div>
        <div className="px-6 py-4 bg-gray-50 dark:bg-neutral-900 border-t dark:border-neutral-700 flex justify-end">
          <Button onClick={onClose} variant="outline">Fechar</Button>
        </div>
      </div>
    </div>
  );
}
