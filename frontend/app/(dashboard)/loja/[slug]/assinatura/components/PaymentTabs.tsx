'use client';

import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CreditCard, Download, Copy } from 'lucide-react';

interface Props {
  boletoUrl?: string;
  pixQrCode?: string;
  pixCopyPaste?: string;
  proximoPagamentoId?: number;
  asaasPaymentId?: string;
  onBaixarBoleto?: (id: number) => void;
  onCopiarPix?: () => void;
}

export function PaymentTabs({ boletoUrl, pixQrCode, pixCopyPaste, proximoPagamentoId, asaasPaymentId, onBaixarBoleto, onCopiarPix }: Props) {
  return (
    <Tabs defaultValue={boletoUrl ? 'boleto' : 'pix'}>
      <TabsList className="w-full sm:w-auto dark:bg-neutral-700">
        {boletoUrl && <TabsTrigger value="boleto" className="flex-1 sm:flex-none">Boleto</TabsTrigger>}
        {(pixQrCode || pixCopyPaste) && <TabsTrigger value="pix" className="flex-1 sm:flex-none">PIX</TabsTrigger>}
      </TabsList>

      {boletoUrl && (
        <TabsContent value="boleto" className="space-y-4 pt-4">
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => window.open(boletoUrl, '_blank')}>
              <CreditCard className="w-4 h-4 mr-2" /> Abrir boleto
            </Button>
            {asaasPaymentId && proximoPagamentoId && onBaixarBoleto && (
              <Button onClick={() => onBaixarBoleto(proximoPagamentoId)}>
                <Download className="w-4 h-4 mr-2" /> Baixar PDF
              </Button>
            )}
          </div>
        </TabsContent>
      )}

      {(pixQrCode || pixCopyPaste) && (
        <TabsContent value="pix" className="space-y-4 pt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {pixQrCode && (
              <div className="text-center">
                <h4 className="font-medium mb-2 dark:text-gray-200">QR Code PIX</h4>
                <div className="bg-white dark:bg-neutral-700 p-4 rounded border dark:border-neutral-600 inline-block">
                  <Image src={`data:image/png;base64,${pixQrCode}`} alt="QR Code PIX" width={192} height={192} className="w-32 h-32 sm:w-48 sm:h-48" unoptimized />
                </div>
              </div>
            )}
            <div>
              <h4 className="font-medium mb-2 dark:text-gray-200">Código PIX (copia e cola)</h4>
              <div className="bg-muted dark:bg-neutral-700 p-3 rounded text-sm font-mono break-all dark:text-gray-200 max-h-32 overflow-y-auto">
                {pixCopyPaste || '—'}
              </div>
              {pixCopyPaste && onCopiarPix && (
                <Button variant="outline" className="mt-2" onClick={onCopiarPix}>
                  <Copy className="w-4 h-4 mr-2" /> Copiar código
                </Button>
              )}
            </div>
          </div>
        </TabsContent>
      )}
    </Tabs>
  );
}
