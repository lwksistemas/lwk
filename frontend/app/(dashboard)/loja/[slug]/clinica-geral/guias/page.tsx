'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function ClinicaGeralGuiasPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-geral`;

  const itens = [
    { href: `${base}/agenda`, titulo: 'Agenda', texto: 'Clique num horário livre para agendar. No card, confirme, recepcione, remarque ou registre falta.' },
    { href: `${base}/pacientes`, titulo: 'Pacientes', texto: 'Cadastre ficha, convênio, responsável e indicação. A busca do topo leva direto para a lista.' },
    { href: `${base}/configuracoes/agenda`, titulo: 'Horários', texto: 'Defina início, fim e duração dos slots em Configurações → Agenda. A grade e os horários livres seguem essa regra.' },
    { href: `/loja/${slug}/configuracoes/whatsapp`, titulo: 'WhatsApp', texto: 'Conecte o número da clínica para confirmações e lembretes.' },
  ];

  return (
    <div className="mx-auto max-w-2xl space-y-4 p-8">
      <h1 className="text-xl font-semibold text-slate-800">Guias de uso</h1>
      <div className="space-y-3">
        {itens.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="block rounded-xl border border-slate-200 bg-white p-5 hover:border-teal-500"
          >
            <h2 className="text-sm font-semibold text-slate-800">{item.titulo}</h2>
            <p className="mt-1 text-sm text-slate-500">{item.texto}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
