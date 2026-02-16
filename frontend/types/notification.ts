export interface Notification {
  id: number;
  titulo: string;
  mensagem: string;
  tipo: string;
  canal: string;
  status: 'pendente' | 'enviado' | 'falhou' | 'lido';
  created_at: string;
  sent_at?: string | null;
  read_at?: string | null;
  metadata?: Record<string, unknown> | null;
}
