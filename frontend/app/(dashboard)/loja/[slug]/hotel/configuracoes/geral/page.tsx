'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { ArrowLeft, Clock, Save, CheckCircle } from 'lucide-react';
import Link from 'next/link';
import apiClient from '@/lib/api-client';

interface ConfiguracaoHotel {
  horario_checkin: string;
  horario_checkout: string;
  politica_cancelamento: string;
  informacoes_adicionais: string;
}

export default function ConfiguracaoGeralHotelPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';

  const [config, setConfig] = useState<ConfiguracaoHotel>({
    horario_checkin: '14:00',
    horario_checkout: '12:00',
    politica_cancelamento: '',
    informacoes_adicionais: '',
  });
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [salvo, setSalvo] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    apiClient.get('/hotel/configuracao/atual/')
      .then(r => setConfig(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const salvar = async () => {
    setSalvando(true);
    setErro('');
    try {
      const r = await apiClient.patch('/hotel/configuracao/atual/', config);
      setConfig(r.data);
      setSalvo(true);
      setTimeout(() => setSalvo(false), 3000);
    } catch {
      setErro('Erro ao salvar. Tente novamente.');
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/15 rounded-lg">
                <Clock className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Configurações Gerais</h1>
                <p className="text-white/80 text-sm">Horários de check-in e check-out</p>
              </div>
            </div>
            <Link
              href={`/loja/${slug}/hotel/configuracoes`}
              className="px-3 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors text-sm flex items-center gap-1"
            >
              <ArrowLeft className="w-4 h-4" /> Voltar
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
          </div>
        ) : (
          <>
            {/* Horários */}
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
              <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <Clock size={18} className="text-sky-600" /> Horários Padrão
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Horário de Check-in
                  </label>
                  <input
                    type="time"
                    value={config.horario_checkin}
                    onChange={e => setConfig(c => ({ ...c, horario_checkin: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">Horário a partir do qual o quarto fica disponível</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Horário de Check-out
                  </label>
                  <input
                    type="time"
                    value={config.horario_checkout}
                    onChange={e => setConfig(c => ({ ...c, horario_checkout: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">Horário limite para desocupação do quarto</p>
                </div>
              </div>
            </div>

            {/* Política de cancelamento */}
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
              <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Política de Cancelamento
              </h2>
              <textarea
                value={config.politica_cancelamento}
                onChange={e => setConfig(c => ({ ...c, politica_cancelamento: e.target.value }))}
                rows={4}
                placeholder="Ex.: Cancelamentos com até 48h de antecedência sem cobrança..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none"
              />
            </div>

            {/* Informações adicionais */}
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
              <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Informações Adicionais
              </h2>
              <textarea
                value={config.informacoes_adicionais}
                onChange={e => setConfig(c => ({ ...c, informacoes_adicionais: e.target.value }))}
                rows={4}
                placeholder="Ex.: Wi-Fi disponível, café da manhã incluso, estacionamento gratuito..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none"
              />
            </div>

            {erro && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">{erro}</p>
            )}

            <button
              onClick={salvar}
              disabled={salvando}
              className="w-full flex items-center justify-center gap-2 py-3 bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white rounded-xl font-semibold transition"
            >
              {salvo ? <CheckCircle size={18} /> : <Save size={18} />}
              {salvando ? 'Salvando...' : salvo ? 'Salvo!' : 'Salvar Configurações'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
