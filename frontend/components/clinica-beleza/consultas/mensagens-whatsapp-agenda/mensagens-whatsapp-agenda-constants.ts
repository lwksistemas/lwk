export const MENSAGEM_WHATSAPP_PLACEHOLDERS = [
  "{nome}",
  "{data}",
  "{hora}",
  "{procedimento}",
  "{profissional}",
  "{link}",
] as const;

export const MENSAGEM_WHATSAPP_PADRAO = `Olá {nome} 😊

Você tem um agendamento:
📅 {data}
⏰ {hora}
💆 {procedimento}
👤 Profissional: {profissional}

Por favor, confirme ou cancele sua consulta:
🔗 {link}

Qualquer dúvida, fale conosco.`;
