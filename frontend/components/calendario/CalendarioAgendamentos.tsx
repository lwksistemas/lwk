'use client';

import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { clinicaApiClient } from '@/lib/api-client';
import { ensureArray } from '@/lib/array-helpers';
import { formatCurrency } from '@/lib/financeiro-helpers';
import { getStatusClinicaInfo, STATUS_AGENDAMENTO_CLINICA } from '@/constants/status';

interface Agendamento {
  id: number;
  cliente_nome: string;
  cliente_telefone: string;
  profissional_nome: string;
  procedimento_nome: string;
  data: string;
  horario: string;
  status: string;
  valor: number;
  observacoes?: string;
}

// Componente de menu de status para agendamentos (portal + delay no fechamento para mobile)
function MenuStatus({ 
  agendamento, 
  onStatusChange 
}: { 
  agendamento: Agendamento; 
  onStatusChange: (agendamento: Agendamento, novoStatus: string) => void;
}) {
  const [showMenu, setShowMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const openTimeRef = useRef<number>(0);

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!showMenu && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setMenuPosition({
        top: rect.bottom + 4,
        left: Math.max(8, Math.min(rect.right - 180, window.innerWidth - 192)),
      });
      openTimeRef.current = Date.now();
    }
    setShowMenu((prev) => !prev);
  };

  const handleClose = () => {
    // No mobile, o mesmo toque pode abrir e fechar; ignorar fechamento nos primeiros 200ms
    if (Date.now() - openTimeRef.current < 250) return;
    setShowMenu(false);
  };

  const handleOptionClick = (e: React.MouseEvent, value: string) => {
    e.stopPropagation();
    e.preventDefault();
    onStatusChange(agendamento, value);
    setShowMenu(false);
  };

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={handleToggle}
        className="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors touch-manipulation"
        title="Mudar status"
        aria-haspopup="true"
        aria-expanded={showMenu}
      >
        <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      
      {showMenu && typeof document !== 'undefined' && createPortal(
        <>
          <div 
            className="fixed inset-0 z-[9998]" 
            onClick={handleClose}
            aria-hidden="true"
          />
          <div 
            className="fixed z-[9999] bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 min-w-[180px] py-1"
            style={{
              top: menuPosition.top,
              left: menuPosition.left,
            }}
            role="menu"
          >
            {STATUS_AGENDAMENTO_CLINICA.map((option) => (
              <button
                key={option.value}
                type="button"
                role="menuitem"
                onClick={(e) => handleOptionClick(e, option.value)}
                className={`w-full text-left px-4 py-3 min-h-[44px] text-sm hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg flex items-center gap-2 touch-manipulation ${
                  option.value === agendamento.status ? 'font-bold bg-gray-50 dark:bg-gray-700/50' : ''
                }`}
              >
                <span style={{ color: option.color }}>●</span>
                {option.label}
              </button>
            ))}
          </div>
        </>,
        document.body
      )}
    </div>
  );
}

interface BloqueioAgenda {
  id: number;
  titulo: string;
  tipo: string;
  tipo_nome?: string;
  data_inicio: string;
  data_fim: string;
  horario_inicio?: string | null;
  horario_fim?: string | null;
  profissional?: number | null;
  profissional_nome?: string | null;
  observacoes?: string;
  is_active?: boolean;
}

interface HorarioTrabalho {
  dia_semana: number;
  hora_entrada: string;
  hora_saida: string;
  intervalo_inicio?: string | null;
  intervalo_fim?: string | null;
  ativo?: boolean;
}

interface Profissional {
  id: number;
  nome: string;
  horarios_trabalho?: HorarioTrabalho[];
}

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
  cor_secundaria: string;
}

type VisualizacaoTipo = 'dia' | 'semana' | 'mes';

interface CalendarioAgendamentosProps {
  loja: LojaInfo;
  /** Quando true, não renderiza o bloco "📅 Calendário" + período + legenda (o pai coloca no menu superior) */
  headerInBar?: boolean;
  /** Chamado quando o título do período muda (ex: "28 - 6 de fevereiro de 2026") */
  onViewTitleChange?: (title: string) => void;
}

const MOBILE_BREAKPOINT = 640;

export default function CalendarioAgendamentos({ loja, headerInBar = false, onViewTitleChange }: CalendarioAgendamentosProps) {
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [bloqueios, setBloqueios] = useState<BloqueioAgenda[]>([]);
  const [profissionais, setProfissionais] = useState<Profissional[]>([]);
  const [profissionalSelecionado, setProfissionalSelecionado] = useState<string>(''); // '' = todos
  const [isMobile, setIsMobile] = useState(() => typeof window !== 'undefined' && window.innerWidth < MOBILE_BREAKPOINT);
  // No mobile (especialmente agenda página dedicada), só "Dia" é usável; desktop começa em "Semana"
  const [visualizacao, setVisualizacao] = useState<VisualizacaoTipo>(() => {
    if (typeof window !== 'undefined' && window.innerWidth < MOBILE_BREAKPOINT) return 'dia';
    return 'semana';
  });
  const [dataAtual, setDataAtual] = useState(new Date());

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const handle = () => {
      const mobile = mql.matches;
      setIsMobile(mobile);
      if (mobile && headerInBar && visualizacao === 'semana') setVisualizacao('dia');
    };
    mql.addEventListener('change', handle);
    handle();
    return () => mql.removeEventListener('change', handle);
  }, [headerInBar, visualizacao]);
  const [loading, setLoading] = useState(true);
  const [showModalAgendamento, setShowModalAgendamento] = useState(false);
  const [agendamentoSelecionado, setAgendamentoSelecionado] = useState<Agendamento | null>(null);
  const [dataHoraSelecionada, setDataHoraSelecionada] = useState<{data: string, horario: string} | null>(null);
  const [showModalBloqueio, setShowModalBloqueio] = useState(false);

  useEffect(() => {
    carregarProfissionais();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    carregarAgendamentos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataAtual, visualizacao, profissionalSelecionado]);

  // Notificar o pai com o título do período quando mudar (para exibir no menu superior)
  useEffect(() => {
    if (!onViewTitleChange) return;
    const opcoes: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'long', day: visualizacao === 'dia' ? 'numeric' : undefined };
    if (visualizacao === 'semana') {
      const { dataInicio, dataFim } = calcularPeriodo();
      const inicio = new Date(dataInicio);
      const fim = new Date(dataFim);
      onViewTitleChange(`${inicio.getDate()} - ${fim.getDate()} de ${inicio.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}`);
    } else {
      onViewTitleChange(dataAtual.toLocaleDateString('pt-BR', opcoes));
    }
    // calcularPeriodo usa dataAtual e visualizacao (já nas deps)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataAtual, visualizacao, onViewTitleChange]);

  const carregarProfissionais = async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/profissionais/');
      setProfissionais(ensureArray<Profissional>(response.data));
    } catch (error) {
      console.error('Erro ao carregar profissionais:', error);
    }
  };

  const carregarAgendamentos = async () => {
    setLoading(true);
    try {
      const { dataInicio, dataFim } = calcularPeriodo();

      const params: Record<string, string> = {
        data_inicio: dataInicio,
        data_fim: dataFim,
      };
      if (profissionalSelecionado) {
        params.profissional_id = profissionalSelecionado;
      }

      const [agRes, blRes] = await Promise.all([
        clinicaApiClient.get('/clinica/agendamentos/calendario/', { params }),
        clinicaApiClient.get('/clinica/bloqueios/', { params }),
      ]);

      setAgendamentos(ensureArray<Agendamento>(agRes.data));
      setBloqueios(ensureArray<BloqueioAgenda>(blRes.data));
    } catch (error) {
      console.error('Erro ao carregar agendamentos:', error);
    } finally {
      setLoading(false);
    }
  };

  const timeToMinutes = (t?: string | null) => {
    if (!t) return null;
    const [hh, mm] = t.split(':').map((v) => parseInt(v, 10));
    return (hh || 0) * 60 + (mm || 0);
  };

  // Retorna os horários de exibição na semana: se o profissional tiver horarios_trabalho configurados, usa o intervalo coberto por eles; senão 08:00–19:00.
  const getHorariosExibicaoSemana = (): string[] => {
    const prof = profissionalSelecionado ? profissionais.find((p) => String(p.id) === profissionalSelecionado) : null;
    const ht = prof?.horarios_trabalho?.filter((h) => h.ativo !== false);
    if (!ht?.length) {
      return Array.from({ length: 12 }, (_, i) => `${(i + 8).toString().padStart(2, '0')}:00`);
    }
    let minMin = 8 * 60;
    let maxMin = 19 * 60;
    ht.forEach((h) => {
      const ent = timeToMinutes(h.hora_entrada) ?? 8 * 60;
      const sai = timeToMinutes(h.hora_saida) ?? 18 * 60;
      if (ent < minMin) minMin = ent;
      if (sai > maxMin) maxMin = sai;
    });
    const slots: string[] = [];
    for (let m = minMin; m <= maxMin; m += 30) {
      const hh = Math.floor(m / 60);
      const mm = m % 60;
      slots.push(`${hh.toString().padStart(2, '0')}:${mm.toString().padStart(2, '0')}`);
    }
    return slots.length ? slots : ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00'];
  };

  /** Retorna o intervalo do profissional no dia (ex.: almoço) se o slot estiver dentro dele; senão null. */
  const getIntervaloProfissionalAt = (diaSemanaBackend: number, horario: string): { inicio: string; fim: string } | null => {
    const prof = profissionalSelecionado ? profissionais.find((p) => String(p.id) === profissionalSelecionado) : null;
    const ht = prof?.horarios_trabalho?.filter((h) => h.ativo !== false && h.dia_semana === diaSemanaBackend);
    if (!ht?.length) return null;
    const slotMin = timeToMinutes(horario) ?? 0;
    for (const h of ht) {
      if (h.intervalo_inicio == null || h.intervalo_fim == null) continue;
      const iIni = timeToMinutes(h.intervalo_inicio) ?? 0;
      const iFim = timeToMinutes(h.intervalo_fim) ?? 0;
      if (slotMin >= iIni && slotMin < iFim) return { inicio: h.intervalo_inicio, fim: h.intervalo_fim };
    }
    return null;
  };

  // Verifica se o slot (ex.: "09:00") está dentro do horário de atendimento do profissional no dia da semana (backend: 0=Seg … 6=Dom).
  const slotDentroDoHorarioProfissional = (diaSemanaBackend: number, horario: string): boolean => {
    const prof = profissionalSelecionado ? profissionais.find((p) => String(p.id) === profissionalSelecionado) : null;
    const ht = prof?.horarios_trabalho?.filter((h) => h.ativo !== false && h.dia_semana === diaSemanaBackend);
    if (!ht?.length) return true;
    const slotMin = timeToMinutes(horario) ?? 0;
    for (const h of ht) {
      const ent = timeToMinutes(h.hora_entrada) ?? 0;
      const sai = timeToMinutes(h.hora_saida) ?? 24 * 60;
      let ini = ent;
      let fim = sai;
      if (h.intervalo_inicio != null && h.intervalo_fim != null) {
        const iIni = timeToMinutes(h.intervalo_inicio) ?? ent;
        const iFim = timeToMinutes(h.intervalo_fim) ?? sai;
        if (slotMin < iIni) fim = iIni;
        else if (slotMin >= iFim) ini = iFim;
        else continue;
      }
      if (slotMin >= ini && slotMin < fim) return true;
    }
    return false;
  };

  // Mapeia dia da semana JS (0=Dom, 1=Seg, …) para backend (0=Seg, …, 6=Dom).
  const jsDayToBackend = (jsDay: number) => (jsDay + 6) % 7;

  /** Dias da semana em que o profissional selecionado atende (backend: 0=Seg … 6=Dom). Se nenhum profissional ou "Todos", retorna todos. */
  const getDiasAtivosProfissional = (): number[] => {
    if (!profissionalSelecionado) return [0, 1, 2, 3, 4, 5, 6];
    const prof = profissionais.find((p) => String(p.id) === profissionalSelecionado);
    const ativos = prof?.horarios_trabalho?.filter((h) => h.ativo !== false).map((h) => h.dia_semana) ?? [];
    if (ativos.length === 0) return [0, 1, 2, 3, 4, 5, 6];
    return [...new Set(ativos)].sort((a, b) => a - b);
  };

  const bloqueioDeveSerExibido = (bloqueio: BloqueioAgenda) => {
    // Se não tem profissional, é global - sempre exibir
    if (!bloqueio.profissional) return true;
    
    // Se não há filtro (Todos), exibir todos os bloqueios
    if (!profissionalSelecionado) return true;
    
    // Se há filtro, exibir apenas bloqueios do profissional selecionado ou globais
    return profissionalSelecionado === String(bloqueio.profissional);
  };

  const bloqueioImpedeCriacaoNoContextoAtual = (bloqueio: BloqueioAgenda) => {
    // Se não tem profissional, é global (impede sempre).
    if (!bloqueio.profissional) return true;
    
    // Se não há filtro (Todos): não impedir criação (pois pode agendar com outro profissional)
    if (!profissionalSelecionado) return false;
    
    // Se há filtro: impedir apenas se for o profissional selecionado
    return profissionalSelecionado === String(bloqueio.profissional);
  };

  const getBloqueioAt = (dataStr: string, horario: string) => {
    const slotMin = timeToMinutes(horario) ?? 0;
    
    // Filtrar bloqueios que devem ser exibidos no contexto atual
    const bloqueiosVisiveis = bloqueios.filter(bloqueioDeveSerExibido);
    
    return bloqueiosVisiveis.find((b) => {
      // Data dentro do intervalo (inclusive)
      if (dataStr < b.data_inicio || dataStr > b.data_fim) return false;

      // Se não informou horário, bloqueia o dia todo
      if (!b.horario_inicio) return true;

      const ini = timeToMinutes(b.horario_inicio);
      if (ini === null) return true;
      const fimRaw = timeToMinutes(b.horario_fim);
      const fim = fimRaw === null ? ini : fimRaw;
      return slotMin >= ini && slotMin <= fim;
    });
  };

  const getBloqueiosDoDia = (dataStr: string) => {
    // Filtrar bloqueios que devem ser exibidos no contexto atual
    const bloqueiosVisiveis = bloqueios.filter(bloqueioDeveSerExibido);
    
    return bloqueiosVisiveis.filter((b) => dataStr >= b.data_inicio && dataStr <= b.data_fim);
  };

  const calcularPeriodo = () => {
    const hoje = new Date(dataAtual);
    let dataInicio: string;
    let dataFim: string;

    switch (visualizacao) {
      case 'dia':
        dataInicio = dataFim = formatarData(hoje);
        break;
      
      case 'semana':
        const inicioSemana = new Date(hoje);
        inicioSemana.setDate(hoje.getDate() - hoje.getDay());
        const fimSemana = new Date(inicioSemana);
        fimSemana.setDate(inicioSemana.getDate() + 6);
        
        dataInicio = formatarData(inicioSemana);
        dataFim = formatarData(fimSemana);
        break;
      
      case 'mes':
        const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
        const fimMes = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
        
        dataInicio = formatarData(inicioMes);
        dataFim = formatarData(fimMes);
        break;
    }

    return { dataInicio, dataFim };
  };

  const formatarData = (data: Date): string => {
    // ✅ CORREÇÃO: Usar timezone local ao invés de UTC
    // toISOString() converte para UTC, causando mudança de dia
    const ano = data.getFullYear();
    const mes = String(data.getMonth() + 1).padStart(2, '0');
    const dia = String(data.getDate()).padStart(2, '0');
    return `${ano}-${mes}-${dia}`;
  };

  const navegarPeriodo = (direcao: 'anterior' | 'proximo') => {
    const novaData = new Date(dataAtual);
    
    switch (visualizacao) {
      case 'dia':
        novaData.setDate(novaData.getDate() + (direcao === 'proximo' ? 1 : -1));
        break;
      case 'semana':
        novaData.setDate(novaData.getDate() + (direcao === 'proximo' ? 7 : -7));
        break;
      case 'mes':
        novaData.setMonth(novaData.getMonth() + (direcao === 'proximo' ? 1 : -1));
        break;
    }
    
    setDataAtual(novaData);
  };

  const obterTituloPeriodo = (): string => {
    const opcoes: Intl.DateTimeFormatOptions = { 
      year: 'numeric', 
      month: 'long',
      day: visualizacao === 'dia' ? 'numeric' : undefined
    };
    
    if (visualizacao === 'semana') {
      const { dataInicio, dataFim } = calcularPeriodo();
      const inicio = new Date(dataInicio);
      const fim = new Date(dataFim);
      
      return `${inicio.getDate()} - ${fim.getDate()} de ${inicio.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}`;
    }
    
    return dataAtual.toLocaleDateString('pt-BR', opcoes);
  };

  const handleNovoAgendamento = (data?: string, horario?: string) => {
    setAgendamentoSelecionado(null);
    setDataHoraSelecionada(data && horario ? { data, horario } : null);
    setShowModalAgendamento(true);
  };

  const handleEditarAgendamento = (agendamento: Agendamento) => {
    setAgendamentoSelecionado(agendamento);
    setDataHoraSelecionada(null);
    setShowModalAgendamento(true);
  };

  const handleExcluirAgendamento = async (agendamento: Agendamento) => {
    if (!confirm(`Tem certeza que deseja excluir o agendamento de ${agendamento.cliente_nome}?`)) {
      return;
    }

    try {
      await clinicaApiClient.delete(`/clinica/agendamentos/${agendamento.id}/`);
      alert('✅ Agendamento excluído com sucesso!');
      carregarAgendamentos();
    } catch (error: unknown) {
      console.error('Erro ao excluir agendamento:', error);
      const msg = (error as { response?: { data?: { error?: string; detail?: string } } })?.response?.data?.error
        || (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg ? `❌ ${msg}` : '❌ Erro ao excluir agendamento');
    }
  };

  const handleMudarStatus = async (agendamento: Agendamento, novoStatus: string) => {
    try {
      await clinicaApiClient.patch(`/clinica/agendamentos/${agendamento.id}/`, { status: novoStatus });
      alert('✅ Status atualizado com sucesso!');
      carregarAgendamentos();
    } catch (error: unknown) {
      console.error('Erro ao atualizar status:', error);
      const msg = (error as { response?: { data?: { error?: string; detail?: string } } })?.response?.data?.error
        || (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg ? `❌ ${msg}` : '❌ Erro ao atualizar status');
    }
  };

  const handleExcluirBloqueio = async (bloqueioId: number) => {
    if (!confirm('Tem certeza que deseja excluir este bloqueio?')) {
      return;
    }

    try {
      await clinicaApiClient.delete(`/clinica/bloqueios/${bloqueioId}/`);
      alert('✅ Bloqueio excluído com sucesso!');
      carregarAgendamentos();
    } catch (error) {
      console.error('Erro ao excluir bloqueio:', error);
      alert('❌ Erro ao excluir bloqueio');
    }
  };

  const renderizarVisualizacao = () => {
    switch (visualizacao) {
      case 'dia':
        return <VisualizacaoDia />;
      case 'semana':
        return <VisualizacaoSemana />;
      case 'mes':
        return <VisualizacaoMes />;
    }
  };

  // Componente para visualização por dia
  const VisualizacaoDia = () => {
    const agendamentosDoDia = agendamentos.filter(ag => ag.data === formatarData(dataAtual));
    const diaBackendDia = jsDayToBackend(dataAtual.getDay());
    const diasAtivos = getDiasAtivosProfissional();
    const profissionalAtendeNesteDia = !profissionalSelecionado || diasAtivos.includes(diaBackendDia);
    const horariosPadrao = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);
    const horarios = horariosPadrao;

    if (profissionalSelecionado && !profissionalAtendeNesteDia) {
      return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-3 sm:p-4 border-b dark:border-gray-700">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Agendamentos do Dia</h3>
          </div>
          <div className="p-6 sm:p-8 text-center">
            <p className="text-gray-500 dark:text-gray-400 mb-2">Este profissional não atende neste dia.</p>
            <p className="text-sm text-gray-400 dark:text-gray-500">Configure os dias de atendimento em Gerenciar Profissionais → Configurar horários.</p>
            {agendamentosDoDia.length > 0 && (
              <div className="mt-6 text-left border-t dark:border-gray-700 pt-4">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Agendamentos existentes neste dia:</p>
                <div className="space-y-2">
                  {agendamentosDoDia.map((ag) => (
                    <div
                      key={ag.id}
                      className="p-2.5 rounded-lg border-l-4 cursor-pointer hover:opacity-80"
                      style={{ backgroundColor: `${getStatusClinicaInfo(ag.status).color}20`, borderLeftColor: getStatusClinicaInfo(ag.status).color }}
                      onClick={() => handleEditarAgendamento(ag)}
                    >
                      <span className="font-medium">{ag.cliente_nome}</span> — {ag.horario} · {ag.procedimento_nome}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-3 sm:p-4 border-b dark:border-gray-700">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Agendamentos do Dia</h3>
        </div>
        <div className="p-3 sm:p-4">
          <div className="space-y-2">
            {horarios.map(horario => {
              const agendamento = agendamentosDoDia.find(ag => ag.horario.startsWith(horario.split(':')[0]));
              const dataStr = formatarData(dataAtual);
              const bloqueio = getBloqueioAt(dataStr, horario);
              const bloqueiaNoContexto = bloqueio ? bloqueioImpedeCriacaoNoContextoAtual(bloqueio) : false;
              const dentroHorarioDia = slotDentroDoHorarioProfissional(diaBackendDia, horario);
              const intervaloAt = getIntervaloProfissionalAt(diaBackendDia, horario);
              
              return (
                <div key={horario} className="flex items-stretch gap-2 sm:gap-4 border-b dark:border-gray-700 pb-2 min-h-[52px]">
                  <div className="w-12 sm:w-16 flex-shrink-0 text-xs sm:text-sm text-gray-600 dark:text-gray-400 font-mono pt-2">
                    {horario}
                  </div>
                  <div className="flex-1 min-w-0">
                    {agendamento ? (
                      <div 
                        className="p-2.5 sm:p-3 rounded-lg cursor-pointer hover:opacity-80 border-l-4 active:scale-[0.99]"
                        style={{ 
backgroundColor: `${getStatusClinicaInfo(agendamento.status).color}20`,
                          borderLeftColor: getStatusClinicaInfo(agendamento.status).color
                        }}
                        onClick={() => handleEditarAgendamento(agendamento)}
                      >
                        <div className="flex justify-between items-start gap-2">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1.5 mb-0.5">
                              <span className="text-base sm:text-lg">{getStatusClinicaInfo(agendamento.status).emoji}</span>
                              <p className="font-semibold text-gray-900 dark:text-white text-sm sm:text-base truncate">{agendamento.cliente_nome}</p>
                            </div>
                            <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 truncate">{agendamento.procedimento_nome}</p>
                            <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 truncate">Prof: {agendamento.profissional_nome}</p>
                            <p className="text-[10px] sm:text-xs font-medium mt-0.5" style={{ color: getStatusClinicaInfo(agendamento.status).color }}>
                              {getStatusClinicaInfo(agendamento.status).label}
                            </p>
                          </div>
                          <div className="flex flex-shrink-0 gap-1 sm:space-x-2">
                            <MenuStatus 
                              agendamento={agendamento}
                              onStatusChange={handleMudarStatus}
                            />
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEditarAgendamento(agendamento);
                              }}
                              className="text-blue-600 hover:text-blue-800 text-sm"
                            >
                              ✏️
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleExcluirAgendamento(agendamento);
                              }}
                              className="text-red-600 hover:text-red-800 text-sm"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      </div>
                    ) : intervaloAt ? (
                      <div
                        className="p-3 rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-700 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200"
                        title={`Intervalo do profissional: ${intervaloAt.inicio} – ${intervaloAt.fim}`}
                      >
                        <div className="font-semibold">🍽️ Intervalo</div>
                        <div className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">{intervaloAt.inicio} – {intervaloAt.fim}</div>
                      </div>
                    ) : bloqueio ? (
                      <div
                        className={`p-3 rounded-lg border text-red-800 dark:text-red-300 ${
                          bloqueiaNoContexto ? 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/30' : 'border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/30'
                        }`}
                        title={bloqueio.observacoes || bloqueio.titulo}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div className="font-semibold">
                            {bloqueiaNoContexto ? '⛔ Bloqueado' : '⚠️ Bloqueio (profissional)'}
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleExcluirBloqueio(bloqueio.id);
                            }}
                            className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 text-sm"
                            title="Excluir bloqueio"
                          >
                            🗑️
                          </button>
                        </div>
                        <div className="text-xs">
                          {bloqueio.titulo}{' '}
                          {bloqueio.profissional_nome ? `(Prof: ${bloqueio.profissional_nome})` : ''}
                        </div>
                        {!bloqueiaNoContexto && (
                          <div className="mt-2">
                            <button
                              onClick={() => handleNovoAgendamento(formatarData(dataAtual), horario)}
                              className="w-full p-2 text-left text-gray-500 dark:text-gray-400 hover:bg-white/60 dark:hover:bg-gray-700/60 rounded border border-dashed border-amber-300 dark:border-amber-700"
                            >
                              + Agendar com outro profissional
                            </button>
                          </div>
                        )}
                      </div>
                    ) : !dentroHorarioDia ? (
                      <div
                        className="w-full p-2 text-left text-gray-400 dark:text-gray-500 rounded border border-dashed border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/30 text-sm"
                        title="Fora do horário de atendimento do profissional"
                      >
                        — Fora do horário
                      </div>
                    ) : (
                      <button
                        onClick={() => handleNovoAgendamento(formatarData(dataAtual), horario)}
                        className="w-full p-2 text-left text-gray-400 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded border-2 border-dashed border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500"
                      >
                        + Agendar
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  // Componente para visualização por semana - ocupa tela inteira; colunas preenchem largura; células grandes para agendar
  // Com profissional selecionado: só exibe colunas dos dias em que ele atende (não configurados ficam de fora)
  const VisualizacaoSemana = () => {
    const { dataInicio } = calcularPeriodo();
    const inicioSemana = new Date(dataInicio);
    const diasSemana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
    const horarios = getHorariosExibicaoSemana();
    const diasAtivos = getDiasAtivosProfissional();
    const diasParaExibir = Array.from({ length: 7 }, (_, i) => {
      const dia = new Date(inicioSemana);
      dia.setDate(inicioSemana.getDate() + i);
      return { dia, backendDay: jsDayToBackend(dia.getDay()) };
    }).filter(({ backendDay }) => diasAtivos.includes(backendDay));

    const gridCols = `minmax(56px, 72px) repeat(${diasParaExibir.length}, minmax(120px, 1fr))`;

    return (
      <div className="flex-1 min-h-0 flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="flex-1 min-h-0 flex flex-col overflow-auto" style={{ WebkitOverflowScrolling: 'touch' }}>
          {/* Cabeçalho dos dias - coluna hora + dias; colunas com 1fr para preencher a tela */}
          <div className="grid border-b dark:border-gray-700 flex-shrink-0" style={{ gridTemplateColumns: gridCols }}>
            <div className="sticky left-0 z-10 bg-white dark:bg-gray-800 p-3 sm:p-4 text-sm font-semibold text-gray-600 dark:text-gray-400 border-r dark:border-gray-700">Hora</div>
            {diasParaExibir.map(({ dia }, idx) => (
              <div key={idx} className="p-3 sm:p-4 text-center border-l dark:border-gray-700">
                <div className="text-xs sm:text-sm font-semibold text-gray-900 dark:text-white">
                  {diasSemana[dia.getDay()]}
                </div>
                <div className="text-lg sm:text-xl font-bold mt-0.5" style={{ color: loja.cor_primaria }}>
                  {dia.getDate()}
                </div>
              </div>
            ))}
          </div>

          {/* Grade de horários - células altas (min 72px) para facilitar toque/agendamento */}
          {horarios.map(horario => (
            <div key={horario} className="grid border-b dark:border-gray-700 flex-shrink-0" style={{ gridTemplateColumns: gridCols }}>
              <div className="sticky left-0 z-10 p-3 sm:p-4 text-sm text-gray-600 dark:text-gray-400 font-mono border-r dark:border-gray-700 bg-white dark:bg-gray-800">
                {horario}
              </div>
              {diasParaExibir.map(({ dia }, idx) => {
                const dataStr = formatarData(dia);
                const diaBackend = jsDayToBackend(dia.getDay());
                const dentroHorario = slotDentroDoHorarioProfissional(diaBackend, horario);
                const intervaloAt = getIntervaloProfissionalAt(diaBackend, horario);
                
                const agendamento = agendamentos.find(ag => 
                  ag.data === dataStr && ag.horario.startsWith(horario.split(':')[0])
                );
                const bloqueio = getBloqueioAt(dataStr, horario);
                const bloqueiaNoContexto = bloqueio ? bloqueioImpedeCriacaoNoContextoAtual(bloqueio) : false;

                return (
                  <div key={idx} className="p-3 sm:p-4 border-l dark:border-gray-700 min-h-[72px] sm:min-h-[80px] relative group">
                    {agendamento ? (
                      <div
                        className="p-2 rounded text-xs cursor-pointer hover:opacity-80 border-l-2 relative"
                        style={{ 
backgroundColor: `${getStatusClinicaInfo(agendamento.status).color}20`,
                          borderLeftColor: getStatusClinicaInfo(agendamento.status).color
                        }}
                        onClick={() => handleEditarAgendamento(agendamento)}
                      >
                        <div className="flex items-center justify-between gap-1 mb-1">
                          <div className="flex items-center gap-1 flex-1 min-w-0">
                            <span>{getStatusClinicaInfo(agendamento.status).emoji}</span>
                            <div className="font-semibold truncate">{agendamento.cliente_nome}</div>
                          </div>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <MenuStatus 
                              agendamento={agendamento}
                              onStatusChange={handleMudarStatus}
                            />
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleExcluirAgendamento(agendamento);
                              }}
                              className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded"
                              title="Excluir"
                            >
                              <svg className="w-3 h-3 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </div>
                        <div className="truncate text-gray-600 dark:text-gray-400">{agendamento.procedimento_nome}</div>
                        <div className="text-[10px] font-medium mt-1" style={{ color: getStatusClinicaInfo(agendamento.status).color }}>
                          {getStatusClinicaInfo(agendamento.status).label}
                        </div>
                      </div>
                    ) : intervaloAt ? (
                      <div
                        className="p-2 rounded text-xs border border-amber-200 bg-amber-50 dark:border-amber-700 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200"
                        title={`Intervalo: ${intervaloAt.inicio} – ${intervaloAt.fim}`}
                      >
                        <div className="font-semibold truncate">🍽️ Intervalo</div>
                        <div className="text-[10px] truncate">{intervaloAt.inicio}–{intervaloAt.fim}</div>
                      </div>
                    ) : bloqueio ? (
                      <div
                        className={`p-2 rounded text-xs border text-red-800 dark:text-red-300 ${
                          bloqueiaNoContexto ? 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/30' : 'border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/30'
                        }`}
                        title={bloqueio.observacoes || bloqueio.titulo}
                      >
                        <div className="flex justify-between items-start mb-1">
                          <div className="font-semibold truncate flex-1">
                            {bloqueiaNoContexto ? '⛔ Bloqueado' : '⚠️ Bloqueio'}
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleExcluirBloqueio(bloqueio.id);
                            }}
                            className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 ml-1"
                            title="Excluir bloqueio"
                          >
                            🗑️
                          </button>
                        </div>
                        <div className="truncate">{bloqueio.titulo}</div>
                      </div>
                    ) : !dentroHorario ? (
                      <div
                        className="w-full min-h-[72px] sm:min-h-[80px] rounded bg-gray-100 dark:bg-gray-700/50 border border-dashed border-gray-200 dark:border-gray-600 flex items-center justify-center text-gray-400 dark:text-gray-500 text-sm"
                        title="Fora do horário de atendimento do profissional"
                      >
                        —
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleNovoAgendamento(dataStr, horario)}
                        className="w-full min-h-[72px] sm:min-h-[80px] flex items-center justify-center text-2xl sm:text-3xl text-gray-300 dark:text-gray-600 hover:text-gray-600 dark:hover:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded border-2 border-dashed border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 touch-manipulation"
                        title="Clique para agendar"
                      >
                        +
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Componente para visualização por mês
  const VisualizacaoMes = () => {
    const ano = dataAtual.getFullYear();
    const mes = dataAtual.getMonth();
    const primeiroDia = new Date(ano, mes, 1);
    const ultimoDia = new Date(ano, mes + 1, 0);
    const diasNoMes = ultimoDia.getDate();
    const diaSemanaInicio = primeiroDia.getDay();

    const dias = [];
    
    // Dias vazios do início
    for (let i = 0; i < diaSemanaInicio; i++) {
      dias.push(null);
    }
    
    // Dias do mês
    for (let dia = 1; dia <= diasNoMes; dia++) {
      dias.push(dia);
    }

    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-3 sm:p-4 border-b dark:border-gray-700">
          <div className="grid grid-cols-7 gap-1 sm:gap-2">
            {['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'].map(dia => (
              <div key={dia} className="text-center text-[10px] sm:text-sm font-semibold text-gray-600 dark:text-gray-400 p-1 sm:p-2">
                {dia}
              </div>
            ))}
          </div>
        </div>
        
        <div className="p-2 sm:p-4">
          <div className="grid grid-cols-7 gap-1 sm:gap-2">
            {dias.map((dia, index) => {
              if (!dia) {
                return <div key={index} className="h-16 sm:h-24"></div>;
              }

              const dataStr = formatarData(new Date(ano, mes, dia));
              const agendamentosDoDia = agendamentos.filter(ag => ag.data === dataStr);
              const bloqueiosDoDia = getBloqueiosDoDia(dataStr);
              const bloqueiosQueImpedem = bloqueiosDoDia.filter(bloqueioImpedeCriacaoNoContextoAtual);
              const diaBloqueadoTotal = bloqueiosQueImpedem.some((b) => !b.horario_inicio);

              return (
                <div
                  key={dia}
                  className={`min-h-[64px] sm:h-24 border dark:border-gray-700 rounded p-1 cursor-pointer active:scale-[0.98] ${
                    diaBloqueadoTotal ? 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-800' : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                  onClick={() => {
                    if (diaBloqueadoTotal) return;
                    handleNovoAgendamento(dataStr, '09:00');
                  }}
                >
                  <div className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                    {dia}
                  </div>
                  <div className="space-y-1">
                    {bloqueiosDoDia.length > 0 && (
                      <div className="text-[10px] px-1 py-0.5 rounded bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300">
                        ⛔ {bloqueiosDoDia.length} bloqueio(s)
                      </div>
                    )}
                    {agendamentosDoDia.slice(0, 2).map(agendamento => (
                      <div
                        key={agendamento.id}
                        className="text-xs p-1 rounded truncate cursor-pointer border-l-2"
                        style={{ 
backgroundColor: `${getStatusClinicaInfo(agendamento.status).color}15`,
                          borderLeftColor: getStatusClinicaInfo(agendamento.status).color
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditarAgendamento(agendamento);
                        }}
                      >
                        <span className="mr-1">{getStatusClinicaInfo(agendamento.status).emoji}</span>
                        {agendamento.horario} {agendamento.cliente_nome}
                      </div>
                    ))}
                    {agendamentosDoDia.length > 2 && (
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        +{agendamentosDoDia.length - 2} mais
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-3 sm:space-y-6 min-h-0 min-w-0 flex flex-col h-full max-w-full overflow-hidden">
      <div className={`${headerInBar ? '' : 'bg-white dark:bg-gray-800 rounded-xl shadow p-3 sm:p-6'} flex-shrink-0`}>
        <div className={`flex flex-col ${headerInBar ? 'gap-2' : 'gap-3 sm:gap-4'}`}>
          {/* Título + período + legenda: só quando não está no menu superior (headerInBar) */}
          {!headerInBar && (
            <div>
              <h2 className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
                📅 Calendário
              </h2>
              <p className="text-xs sm:text-base text-gray-600 dark:text-gray-400 mt-0.5">{obterTituloPeriodo()}</p>
              <div className="hidden sm:flex flex-wrap gap-3 mt-3">
                <div className="flex items-center gap-1 text-xs"><span>🔵</span><span className="text-gray-600 dark:text-gray-400">Agendado</span></div>
                <div className="flex items-center gap-1 text-xs"><span>🟢</span><span className="text-gray-600 dark:text-gray-400">Confirmado</span></div>
                <div className="flex items-center gap-1 text-xs"><span>🔴</span><span className="text-gray-600 dark:text-gray-400">Faltou</span></div>
                <div className="flex items-center gap-1 text-xs"><span>⚪</span><span className="text-gray-600 dark:text-gray-400">Cancelado</span></div>
              </div>
            </div>
          )}
          {/* Filtro profissional + Dia/Semana/Mês + Navegação - empilhado no mobile */}
          <div className="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2">
            <select
              value={profissionalSelecionado}
              onChange={(e) => setProfissionalSelecionado(e.target.value)}
              className="w-full sm:flex-1 sm:min-w-[120px] min-h-[44px] px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white touch-manipulation"
              title="Filtrar por profissional"
            >
              <option value="">Todos os profissionais</option>
              {profissionais.map((p) => (
                <option key={p.id} value={String(p.id)}>
                  {p.nome}
                </option>
              ))}
            </select>
            {profissionalSelecionado && (() => {
              const slots = getHorariosExibicaoSemana();
              if (!slots.length) return null;
              return (
                <span className="text-xs text-gray-600 dark:text-gray-400 self-center" title="Horário configurado do profissional">
                  Horário: {slots[0]} – {slots[slots.length - 1]}
                </span>
              );
            })()}
            <div className="flex rounded-lg border border-gray-300 dark:border-gray-600 overflow-hidden touch-manipulation">
              {(isMobile && headerInBar ? ['dia', 'mes'] : ['dia', 'semana', 'mes']).map((tipo) => (
                <button
                  key={tipo}
                  onClick={() => setVisualizacao(tipo as VisualizacaoTipo)}
                  className={`flex-1 min-h-[44px] px-2 sm:px-4 py-2 text-xs sm:text-sm font-medium capitalize ${
                    visualizacao === tipo
                      ? 'text-white'
                      : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                  }`}
                  style={{
                    backgroundColor: visualizacao === tipo ? loja.cor_primaria : 'transparent'
                  }}
                >
                  {tipo === 'mes' ? 'Mês' : tipo === 'semana' ? 'Semana' : 'Dia'}
                </button>
              ))}
            </div>
            <div className="flex rounded-lg border border-gray-300 dark:border-gray-600 overflow-hidden touch-manipulation">
              <button
                onClick={() => navegarPeriodo('anterior')}
                className="min-h-[44px] min-w-[44px] flex items-center justify-center border-r border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white"
                aria-label="Período anterior"
              >
                ←
              </button>
              <button
                onClick={() => setDataAtual(new Date())}
                className="min-h-[44px] px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm font-medium text-gray-900 dark:text-white"
              >
                Hoje
              </button>
              <button
                onClick={() => navegarPeriodo('proximo')}
                className="min-h-[44px] min-w-[44px] flex items-center justify-center border-l border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white"
                aria-label="Próximo período"
              >
                →
              </button>
            </div>
          </div>

          {/* Botões na mesma linha; no mobile menores para caber junto */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleNovoAgendamento()}
              className="min-h-[44px] flex-1 min-w-0 px-3 py-2 sm:px-4 sm:py-2.5 text-white rounded-lg hover:opacity-90 text-xs sm:text-sm font-medium touch-manipulation"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Novo Agendamento
            </button>
            <button
              onClick={() => setShowModalBloqueio(true)}
              className="min-h-[44px] flex-1 min-w-0 px-3 py-2 sm:px-4 sm:py-2.5 bg-red-500 text-white rounded-lg hover:bg-red-600 text-xs sm:text-sm font-medium touch-manipulation"
            >
              🚫 Bloquear
            </button>
          </div>
        </div>
      </div>

      {/* Área do calendário - na semana ocupa tela inteira (flex-1); scroll suave no mobile */}
      <div className={`flex-1 min-h-0 min-w-0 overflow-auto overscroll-contain ${visualizacao === 'semana' ? 'flex flex-col' : '-mx-2 px-2 sm:mx-0 sm:px-0'}`} style={{ WebkitOverflowScrolling: 'touch' }}>
        {loading ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 sm:p-12 text-center min-h-[200px] flex items-center justify-center">
            <div className="text-gray-500 dark:text-gray-400 text-sm sm:text-base">Carregando agendamentos...</div>
          </div>
        ) : (
          renderizarVisualizacao()
        )}
      </div>

      {/* Modal de Agendamento */}
      {showModalAgendamento && (
        <ModalAgendamento
          loja={loja}
          agendamento={agendamentoSelecionado}
          dataHoraSelecionada={dataHoraSelecionada}
          onClose={() => setShowModalAgendamento(false)}
          onSuccess={() => {
            carregarAgendamentos();
            setShowModalAgendamento(false);
          }}
        />
      )}

      {/* Modal de Bloqueio */}
      {showModalBloqueio && (
        <ModalBloqueio
          loja={loja}
          profissionais={profissionais}
          profissionalSelecionado={profissionalSelecionado}
          onClose={() => setShowModalBloqueio(false)}
          onSuccess={() => {
            carregarAgendamentos();
            setShowModalBloqueio(false);
          }}
        />
      )}
    </div>
  );
}

// Modal para criar/editar agendamentos
function ModalAgendamento({
  loja,
  agendamento,
  dataHoraSelecionada,
  onClose,
  onSuccess
}: {
  loja: LojaInfo;
  agendamento: Agendamento | null;
  dataHoraSelecionada: {data: string, horario: string} | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    cliente: '',
    profissional: '',
    procedimento: '',
    data: '',
    horario: '',
    valor: '',
    observacoes: ''
  });
  const [clientes, setClientes] = useState<any[]>([]);
  const [profissionais, setProfissionais] = useState<any[]>([]);
  const [procedimentos, setProcedimentos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);

  const horarios = [
    '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
    '11:00', '11:30', '12:00', '12:30', '13:00', '13:30',
    '14:00', '14:30', '15:00', '15:30', '16:00', '16:30',
    '17:00', '17:30', '18:00', '18:30', '19:00'
  ];

  useEffect(() => {
    loadFormData();
    
    if (agendamento) {
      setFormData({
        cliente: agendamento.id.toString(),
        profissional: agendamento.id.toString(),
        procedimento: agendamento.id.toString(),
        data: agendamento.data,
        horario: agendamento.horario,
        valor: agendamento.valor.toString(),
        observacoes: agendamento.observacoes || ''
      });
    } else if (dataHoraSelecionada) {
      setFormData(prev => ({
        ...prev,
        data: dataHoraSelecionada.data,
        horario: dataHoraSelecionada.horario
      }));
    }
  }, [agendamento, dataHoraSelecionada]);

  const loadFormData = async () => {
    try {
      const [clientesRes, profissionaisRes, procedimentosRes] = await Promise.all([
        clinicaApiClient.get('/clinica/clientes/'),
        clinicaApiClient.get('/clinica/profissionais/'),
        clinicaApiClient.get('/clinica/procedimentos/')
      ]);
      
      setClientes(ensureArray<any>(clientesRes.data));
      setProfissionais(ensureArray<any>(profissionaisRes.data));
      setProcedimentos(ensureArray<any>(procedimentosRes.data));
    } catch (error) {
      console.error('Erro ao carregar dados do formulário:', error);
    } finally {
      setLoadingData(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Auto-preencher valor quando procedimento for selecionado
    if (name === 'procedimento' && value) {
      const procedimento = procedimentos.find(p => p.id.toString() === value);
      if (procedimento) {
        setFormData(prev => ({
          ...prev,
          valor: procedimento.preco
        }));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const cleanedData = Object.fromEntries(
        Object.entries(formData).map(([key, value]) => [
          key, 
          value === '' ? null : value
        ])
      );

      if (agendamento) {
        await clinicaApiClient.put(`/clinica/agendamentos/${agendamento.id}/`, cleanedData);
        alert('✅ Agendamento atualizado com sucesso!');
      } else {
        await clinicaApiClient.post('/clinica/agendamentos/', cleanedData);
        alert('✅ Agendamento criado com sucesso!');
      }
      
      onSuccess();
    } catch (error: unknown) {
      console.error('Erro ao salvar agendamento:', error);
      const msg =
        (error as { response?: { data?: { error?: string; detail?: string } } })?.response?.data?.error ||
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (error instanceof Error ? error.message : null);
      alert(msg ? `❌ ${msg}` : '❌ Erro ao salvar agendamento');
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="text-center">Carregando formulário...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          📅 {agendamento ? 'Editar Agendamento' : 'Novo Agendamento'}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Cliente *
              </label>
              <select
                name="cliente"
                value={formData.cliente}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Selecione um cliente...</option>
                {clientes.map(cliente => (
                  <option key={cliente.id} value={cliente.id}>
                    {cliente.nome} - {cliente.telefone}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Profissional *
              </label>
              <select
                name="profissional"
                value={formData.profissional}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Selecione um profissional...</option>
                {profissionais.map(prof => (
                  <option key={prof.id} value={prof.id}>
                    {prof.nome} - {prof.especialidade}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Procedimento *
              </label>
              <select
                name="procedimento"
                value={formData.procedimento}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Selecione um procedimento...</option>
                {procedimentos.map(proc => (
                  <option key={proc.id} value={proc.id}>
                    {proc.nome} - {formatCurrency(proc.preco)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data *
              </label>
              <input
                type="date"
                name="data"
                value={formData.data}
                onChange={handleChange}
                required
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Horário *
              </label>
              <select
                name="horario"
                value={formData.horario}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Selecione...</option>
                {horarios.map(hora => (
                  <option key={hora} value={hora}>{hora}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Valor (R$) *
              </label>
              <input
                type="number"
                name="valor"
                value={formData.valor}
                onChange={handleChange}
                required
                min="0"
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="0.00"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Observações
              </label>
              <textarea
                name="observacoes"
                value={formData.observacoes}
                onChange={handleChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Informações adicionais sobre o agendamento..."
              />
            </div>
          </div>

          <div className="flex justify-end space-x-4 pt-4 border-t dark:border-gray-600">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 text-gray-900 dark:text-white"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              {loading ? 'Salvando...' : (agendamento ? 'Atualizar' : 'Criar Agendamento')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


// Modal para criar bloqueios de horário
function ModalBloqueio({
  loja,
  profissionais,
  profissionalSelecionado,
  onClose,
  onSuccess
}: {
  loja: LojaInfo;
  profissionais: Profissional[];
  profissionalSelecionado: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    tipo: 'periodo', // 'periodo' ou 'dia_completo'
    profissional: '', // Sempre vazio inicialmente - usuário deve escolher explicitamente
    data_inicio: '',
    data_fim: '',
    horario_inicio: '08:00',
    horario_fim: '18:00',
    motivo: ''
  });
  const [loading, setLoading] = useState(false);

  const horarios = [
    '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
    '11:00', '11:30', '12:00', '12:30', '13:00', '13:30',
    '14:00', '14:30', '15:00', '15:30', '16:00', '16:30',
    '17:00', '17:30', '18:00', '18:30', '19:00'
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const bloqueioData: any = {
        titulo: formData.motivo || 'Bloqueio de agenda',
        tipo: formData.tipo === 'dia_completo' ? 'feriado' : 'outros',
        data_inicio: formData.data_inicio,
        data_fim: formData.data_fim,
        observacoes: formData.motivo
      };

      // Adicionar profissional apenas se selecionado
      if (formData.profissional) {
        const profissionalId = parseInt(formData.profissional);
        
        // Validar que o profissional existe na lista carregada
        const profissionalExiste = profissionais.some(p => p.id === profissionalId);
        
        if (!profissionalExiste) {
          alert('❌ Erro: Profissional inválido. Por favor, recarregue a página (Ctrl+Shift+R) e tente novamente.');
          setLoading(false);
          return;
        }
        
        bloqueioData.profissional = profissionalId;
      }

      // Adicionar horários apenas se for período
      if (formData.tipo === 'periodo') {
        bloqueioData.horario_inicio = formData.horario_inicio;
        bloqueioData.horario_fim = formData.horario_fim;
      }

      await clinicaApiClient.post('/clinica/bloqueios/', bloqueioData);
      alert('✅ Bloqueio criado com sucesso!');
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Erro ao criar bloqueio:', error);
      
      // Mensagem de erro mais detalhada
      const errorMessage = error?.response?.data?.profissional?.[0] || 
                          error?.response?.data?.detail || 
                          'Erro ao criar bloqueio';
      
      alert(`❌ ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="border-b dark:border-gray-700 p-6 flex items-center justify-between">
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
            🚫 Bloquear Horário
          </h3>
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white"
          >
            ✕ Fechar
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Tipo de Bloqueio */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Tipo de Bloqueio *
              </label>
              <select
                name="tipo"
                value={formData.tipo}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 
                           bg-white dark:bg-gray-700 
                           text-gray-900 dark:text-white 
                           border border-gray-300 dark:border-gray-600 
                           rounded-md"
              >
                <option value="periodo">Período Específico</option>
                <option value="dia_completo">Dia Completo</option>
              </select>
            </div>

            {/* Profissional */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Profissional
              </label>
              <select
                name="profissional"
                value={formData.profissional}
                onChange={handleChange}
                className="w-full px-3 py-2 
                           bg-white dark:bg-gray-700 
                           text-gray-900 dark:text-white 
                           border border-gray-300 dark:border-gray-600 
                           rounded-md"
              >
                <option value="">Todos os profissionais</option>
                {profissionais.map(prof => (
                  <option key={prof.id} value={prof.id}>
                    {prof.nome}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Deixe em branco para bloquear para todos
              </p>
            </div>

            {/* Data Início */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data Início *
              </label>
              <input
                type="date"
                name="data_inicio"
                value={formData.data_inicio}
                onChange={handleChange}
                required
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 
                           bg-white dark:bg-gray-700 
                           text-gray-900 dark:text-white 
                           border border-gray-300 dark:border-gray-600 
                           rounded-md"
              />
            </div>

            {/* Data Fim */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data Fim *
              </label>
              <input
                type="date"
                name="data_fim"
                value={formData.data_fim}
                onChange={handleChange}
                required
                min={formData.data_inicio || new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 
                           bg-white dark:bg-gray-700 
                           text-gray-900 dark:text-white 
                           border border-gray-300 dark:border-gray-600 
                           rounded-md"
              />
            </div>

            {/* Horário Início (apenas para período) */}
            {formData.tipo === 'periodo' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Horário Início *
                  </label>
                  <select
                    name="horario_inicio"
                    value={formData.horario_inicio}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 
                               bg-white dark:bg-gray-700 
                               text-gray-900 dark:text-white 
                               border border-gray-300 dark:border-gray-600 
                               rounded-md"
                  >
                    {horarios.map(hora => (
                      <option key={hora} value={hora}>{hora}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Horário Fim *
                  </label>
                  <select
                    name="horario_fim"
                    value={formData.horario_fim}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 
                               bg-white dark:bg-gray-700 
                               text-gray-900 dark:text-white 
                               border border-gray-300 dark:border-gray-600 
                               rounded-md"
                  >
                    {horarios.map(hora => (
                      <option key={hora} value={hora}>{hora}</option>
                    ))}
                  </select>
                </div>
              </>
            )}

            {/* Motivo */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Motivo do Bloqueio *
              </label>
              <textarea
                name="motivo"
                value={formData.motivo}
                onChange={handleChange}
                required
                rows={3}
                className="w-full px-3 py-2 
                           bg-white dark:bg-gray-700 
                           text-gray-900 dark:text-white 
                           border border-gray-300 dark:border-gray-600 
                           rounded-md 
                           resize-none"
                placeholder="Ex: Férias, Reunião, Treinamento..."
              />
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 
                         border border-gray-300 dark:border-gray-600 
                         rounded-md 
                         hover:bg-gray-50 dark:hover:bg-gray-700 
                         disabled:opacity-50 
                         text-gray-900 dark:text-white"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              {loading ? 'Criando...' : '🚫 Criar Bloqueio'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
