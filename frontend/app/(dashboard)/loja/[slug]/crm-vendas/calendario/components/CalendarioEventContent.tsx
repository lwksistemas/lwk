'use client';

interface CalendarioEventContentProps {
  eventInfo: {
    event: {
      title: string;
      extendedProps?: { atividade?: { tipo: string; concluido?: boolean }; tipo?: string };
    };
    timeText?: string;
  };
}

export function CalendarioEventContent({ eventInfo }: CalendarioEventContentProps) {
  const atividade = eventInfo.event.extendedProps?.atividade;
  const isFeriado = eventInfo.event.extendedProps?.tipo === 'feriado';

  if (isFeriado) {
    return (
      <div className="fc-event-main-frame">
        <div className="fc-event-title-container">
          <div className="fc-event-title fc-sticky">{eventInfo.event.title}</div>
        </div>
      </div>
    );
  }

  if (!atividade) return null;

  const tipoEmoji: Record<string, string> = {
    call: '📞',
    meeting: '🤝',
    email: '📧',
    task: '✅',
  };

  const emoji = tipoEmoji[atividade.tipo] || '✅';

  return (
    <div className="fc-event-main-frame">
      <div className="fc-event-time">{eventInfo.timeText}</div>
      <div className="fc-event-title-container">
        <div className="fc-event-title fc-sticky">
          <span className="mr-1">{emoji}</span>
          {atividade.concluido && <span className="mr-1">✓</span>}
          {eventInfo.event.title.replace(/^(✓\s*)?(📞|🤝|📧|✅)\s*/, '')}
        </div>
      </div>
    </div>
  );
}
