'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

type LojaRadio = {
  id: number;
  nome: string;
  slug: string;
  cpf_cnpj: string;
  plano: string;
  dicom_contratado: boolean;
  worklist_contratado: boolean;
};

type Contrato = {
  id: number;
  loja: number;
  dicom_contratado: boolean;
  worklist_contratado: boolean;
  cobranca_dicom_mensal: string;
  cobranca_worklist_mensal: string;
  valor_mensal: string;
  is_active: boolean;
};

type Maquina = {
  id: number;
  loja: number;
  loja_nome: string;
  tipo: string;
  tipo_label: string;
  nome: string;
  ae_title: string;
  fabricante: string;
  modelo: string;
  cobranca_mensal: string;
  status: string;
  status_label: string;
  codigo_vinculo: string;
  dicom_vinculado?: boolean;
  numero_serie?: string;
  pacs_ae?: string;
  pacs_host?: string;
  pacs_port?: number;
  is_active: boolean;
};

type PacsInfo = {
  ae_title: string;
  host: string;
  port: number;
};

const TIPOS = [
  { id: 'US', label: 'Ultrassom' },
  { id: 'DX', label: 'Raio-X' },
  { id: 'MG', label: 'Mamógrafo' },
  { id: 'CR', label: 'CR / Digitalizador' },
];

const PRECO_TIPO: Record<string, string> = {
  US: '199.90',
  DX: '249.90',
  MG: '299.90',
  CR: '179.90',
};

export default function MaquinasRadiologiaPage() {
  const router = useRouter();
  const [lojas, setLojas] = useState<LojaRadio[]>([]);
  const [maquinas, setMaquinas] = useState<Maquina[]>([]);
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [pacsInfo, setPacsInfo] = useState<PacsInfo>({ ae_title: 'LWKPACS', host: '201.23.81.50', port: 4242 });
  const [lojaId, setLojaId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [ok, setOk] = useState('');
  const [openMaq, setOpenMaq] = useState(false);
  const [openPacs, setOpenPacs] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    nome: '',
    ae_title: '',
    tipo: 'US',
    fabricante: '',
    modelo: '',
    cobranca_mensal: '199.90',
  });
  const [pacs, setPacs] = useState({
    dicom_contratado: true,
    worklist_contratado: true,
    cobranca_dicom_mensal: '99.90',
    cobranca_worklist_mensal: '99.90',
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [lj, mq, ct, pacsRes] = await Promise.all([
        apiClient.get('/superadmin/maquinas-radiologia/lojas-radiologia/'),
        apiClient.get('/superadmin/maquinas-radiologia/'),
        apiClient.get('/superadmin/contratos-pacs/'),
        apiClient.get('/superadmin/maquinas-radiologia/pacs/'),
      ]);
      const lojaList = Array.isArray(lj.data) ? lj.data : [];
      setLojas(lojaList);
      const mqList = Array.isArray(mq.data) ? mq.data : mq.data?.results || [];
      setMaquinas(mqList);
      const ctList = Array.isArray(ct.data) ? ct.data : ct.data?.results || [];
      setContratos(ctList);
      if (pacsRes.data?.host) {
        setPacsInfo({
          ae_title: pacsRes.data.ae_title || 'LWKPACS',
          host: pacsRes.data.host,
          port: Number(pacsRes.data.port) || 4242,
        });
      }
    } catch {
      setError('Erro ao carregar máquinas / contratos PACS.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    void load();
  }, [load, router]);

  const lojaFiltro = lojas.find((l) => String(l.id) === lojaId);
  const lojaModal = lojaFiltro || (lojas.length === 1 ? lojas[0] : undefined);
  const lojaAlvoId = lojaId || (lojaModal ? String(lojaModal.id) : '');
  const contratoLoja = contratos.find((c) => String(c.loja) === lojaAlvoId);
  const maquinasFiltradas = lojaId ? maquinas.filter((m) => String(m.loja) === lojaId) : maquinas;

  const aplicarContratoDaLoja = (id: string) => {
    const ct = contratos.find((c) => String(c.loja) === id);
    if (ct) {
      setPacs({
        dicom_contratado: ct.dicom_contratado,
        worklist_contratado: ct.worklist_contratado,
        cobranca_dicom_mensal: ct.cobranca_dicom_mensal,
        cobranca_worklist_mensal: ct.cobranca_worklist_mensal,
      });
    } else {
      setPacs({
        dicom_contratado: true,
        worklist_contratado: true,
        cobranca_dicom_mensal: '99.90',
        cobranca_worklist_mensal: '99.90',
      });
    }
  };

  const abrirPacs = () => {
    if (!lojaId && lojas.length === 1) setLojaId(String(lojas[0].id));
    aplicarContratoDaLoja(lojaAlvoId);
    setOpenPacs(true);
  };

  const abrirMaq = () => {
    setForm({
      nome: '',
      ae_title: '',
      tipo: 'US',
      fabricante: '',
      modelo: '',
      cobranca_mensal: PRECO_TIPO.US,
    });
    if (!lojaId && lojas.length === 1) setLojaId(String(lojas[0].id));
    setOpenMaq(true);
  };

  const salvarPacs = async () => {
    const id = lojaAlvoId;
    if (!id) {
      setError('Selecione a clínica no formulário.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const payload = { loja: Number(id), ...pacs, is_active: true };
      const existente = contratos.find((c) => String(c.loja) === id);
      if (existente) {
        await apiClient.patch(`/superadmin/contratos-pacs/${existente.id}/`, payload);
      } else {
        await apiClient.post('/superadmin/contratos-pacs/', payload);
      }
      setOpenPacs(false);
      setOk('Contrato DICOM/Worklist salvo. A mensalidade da clínica foi atualizada.');
      await load();
    } catch {
      setError('Falha ao salvar contrato PACS.');
    } finally {
      setSaving(false);
    }
  };

  const criarMaquina = async () => {
    const id = lojaAlvoId;
    if (!id) {
      setError('Selecione a clínica no formulário.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await apiClient.post('/superadmin/maquinas-radiologia/', {
        loja: Number(id),
        ...form,
        ae_title: form.ae_title.trim().toUpperCase(),
      });
      setOpenMaq(false);
      setOk('Máquina cadastrada. Clique em Liberar para aparecer no sistema do cliente.');
      await load();
    } catch (err: unknown) {
      const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const first = data && typeof data === 'object' ? Object.values(data).flat()[0] : '';
      setError(typeof first === 'string' ? first : 'Falha ao cadastrar máquina.');
    } finally {
      setSaving(false);
    }
  };

  const acao = async (id: number, path: 'liberar' | 'suspender' | 'vincular' | 'novo-codigo') => {
    setError('');
    setOk('');
    try {
      const res = await apiClient.post(`/superadmin/maquinas-radiologia/${id}/${path}/`);
      const valor = res.data?.valor_mensalidade;
      const serial = res.data?.numero_serie || res.data?.equipamento?.numero_serie;
      if (path === 'liberar') {
        setOk(`Máquina liberada no cliente. Código: ${res.data?.codigo_vinculo || ''}${valor ? ` · Mensalidade: R$ ${valor}` : ''}`);
      } else if (path === 'vincular') {
        setOk(serial ? `DICOM vinculado. Serial: ${serial}` : 'Vínculo DICOM processado.');
      } else if (path === 'novo-codigo') {
        setOk(`Novo código: ${res.data?.codigo_vinculo || ''}. Use este Accession no ultrassom.`);
      } else {
        setOk(`Máquina suspensa.${valor ? ` Mensalidade: R$ ${valor}` : ''}`);
      }
      await load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error;
      setError(msg || `Falha ao ${path} máquina.`);
    }
  };

  const selectClinica = (
    <label className="block text-sm">
      Clínica
      <select
        className="mt-1 block w-full rounded-md border px-3 py-2"
        value={lojaAlvoId}
        onChange={(e) => {
          setLojaId(e.target.value);
          if (openPacs) aplicarContratoDaLoja(e.target.value);
        }}
      >
        <option value="">Selecione…</option>
        {lojas.map((l) => (
          <option key={l.id} value={l.id}>
            {l.nome} {l.cpf_cnpj ? `(${l.cpf_cnpj})` : ''}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="bg-gradient-to-r from-teal-800 to-teal-950 text-white">
        <div className="w-full max-w-full px-4 py-5 sm:px-6 lg:px-8">
          <a href="/superadmin/dashboard" className="text-sm text-teal-100 hover:underline">← Dashboard</a>
          <h1 className="mt-2 text-2xl font-bold">Máquinas Radiologia</h1>
          <p className="text-sm text-teal-100">Cadastro, cobrança e liberação de ultrassom, raio-X e mamógrafo</p>
        </div>
      </header>

      <main className="w-full max-w-full px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-4 rounded-xl border border-teal-200 bg-teal-50 p-4 text-sm text-teal-950">
          <p className="font-semibold">Fluxo</p>
          <ol className="mt-1 list-decimal pl-5 text-xs sm:text-sm">
            <li>Contratar <strong>servidor DICOM + Worklist</strong> para a clínica.</li>
            <li>Cadastrar a máquina (US / RX / MG) com preço mensal.</li>
            <li><strong>Liberar</strong> — o aparelho aparece no cliente; status fica <strong>Aguardando exame</strong>.</li>
            <li>No ultrassom, envie um exame de teste com o <strong>código</strong> no Accession Number. Se o aparelho recusar um código já usado, clique em <strong>Novo código</strong>.</li>
            <li><strong>Vincular DICOM</strong> — o sistema lê o serial; status vira <strong>Vinculada</strong>.</li>
            <li>O cliente só <strong>escolhe a máquina ao abrir o exame</strong>.</li>
          </ol>
        </div>

        {ok && <div className="mb-3 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{ok}</div>}
        {error && <div className="mb-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

        <div className="mb-4 flex flex-wrap items-end gap-3">
          <label className="text-sm">
            Clínica
            <select
              className="mt-1 block min-w-[280px] rounded-md border px-3 py-2"
              value={lojaId}
              onChange={(e) => setLojaId(e.target.value)}
            >
              <option value="">Todas</option>
              {lojas.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.nome} {l.cpf_cnpj ? `(${l.cpf_cnpj})` : ''}
                </option>
              ))}
            </select>
          </label>
          {lojaFiltro && (
            <div className="text-xs text-gray-600">
              PACS: {lojaFiltro.dicom_contratado ? 'DICOM sim' : 'DICOM não'} · {lojaFiltro.worklist_contratado ? 'Worklist sim' : 'Worklist não'}
            </div>
          )}
          <div className="rounded-md bg-gray-100 px-3 py-2 font-mono text-xs text-gray-800">
            Servidor {pacsInfo.host} · Porta {pacsInfo.port} · AE {pacsInfo.ae_title}
          </div>
          <button
            type="button"
            className="rounded-md bg-teal-800 px-3 py-2 text-sm text-white"
            onClick={abrirPacs}
          >
            Contrato DICOM / Worklist
          </button>
          <button
            type="button"
            className="rounded-md bg-white px-3 py-2 text-sm font-semibold text-teal-900 ring-1 ring-teal-800"
            onClick={abrirMaq}
          >
            Nova máquina
          </button>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500">Carregando…</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs uppercase text-gray-500">
                  <th className="px-4 py-3">Clínica</th>
                  <th className="px-4 py-3">Máquina</th>
                  <th className="px-4 py-3">Tipo</th>
                  <th className="px-4 py-3">AE Title</th>
                  <th className="px-4 py-3">Servidor</th>
                  <th className="px-4 py-3">Porta</th>
                  <th className="px-4 py-3">R$/mês</th>
                  <th className="px-4 py-3">Código</th>
                  <th className="px-4 py-3">Serial</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {maquinasFiltradas.map((m) => (
                  <tr key={m.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3">{m.loja_nome}</td>
                    <td className="px-4 py-3 font-medium">{m.nome}</td>
                    <td className="px-4 py-3">{m.tipo_label}</td>
                    <td className="px-4 py-3 font-mono text-xs">{m.ae_title}</td>
                    <td className="px-4 py-3 font-mono text-xs">{m.pacs_host || pacsInfo.host}</td>
                    <td className="px-4 py-3 font-mono text-xs">{m.pacs_port || pacsInfo.port}</td>
                    <td className="px-4 py-3">{m.cobranca_mensal}</td>
                    <td className="px-4 py-3 font-mono text-sm font-semibold tracking-wide">{m.codigo_vinculo || '—'}</td>
                    <td className="px-4 py-3 font-mono text-xs">{m.numero_serie || '—'}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${
                        m.dicom_vinculado ? 'bg-emerald-50 text-emerald-800' :
                        m.status === 'liberada' ? 'bg-amber-50 text-amber-800' :
                        m.status === 'suspensa' ? 'bg-red-50 text-red-700' : 'bg-gray-100 text-gray-700'
                      }`}>
                        {m.status_label}
                      </span>
                    </td>
                    <td className="space-x-3 px-4 py-3 text-right text-xs">
                      {m.status !== 'liberada' && (
                        <button type="button" className="font-semibold text-teal-800" onClick={() => void acao(m.id, 'liberar')}>Liberar</button>
                      )}
                      {m.status === 'liberada' && (
                        <>
                          <button type="button" className="font-semibold text-teal-800" onClick={() => void acao(m.id, 'vincular')}>Vincular DICOM</button>
                          <button
                            type="button"
                            className="font-semibold text-teal-800"
                            onClick={() => {
                              if (confirm('Gerar novo código? O código anterior deixa de valer no ultrassom.')) {
                                void acao(m.id, 'novo-codigo');
                              }
                            }}
                          >
                            Novo código
                          </button>
                          <button type="button" className="font-semibold text-red-600" onClick={() => void acao(m.id, 'suspender')}>Suspender</button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
                {!maquinasFiltradas.length && (
                  <tr>
                    <td colSpan={11} className="px-4 py-10 text-center text-gray-500">
                      Nenhuma máquina cadastrada. Clique em <strong>Nova máquina</strong> para incluir.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {openPacs && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-5">
            <h2 className="mb-3 text-lg font-semibold">Contrato servidor DICOM / Worklist</h2>
            <p className="mb-3 text-xs text-gray-500">Obrigatório para liberar máquinas na clínica.</p>
            <div className="mb-3">{selectClinica}</div>
            <label className="mb-2 flex items-center gap-2 text-sm">
              <input type="checkbox" checked={pacs.dicom_contratado} onChange={(e) => setPacs({ ...pacs, dicom_contratado: e.target.checked })} />
              Servidor DICOM (C-STORE)
            </label>
            <input className="mb-3 w-full rounded-md border px-3 py-2" placeholder="R$ DICOM / mês" value={pacs.cobranca_dicom_mensal} onChange={(e) => setPacs({ ...pacs, cobranca_dicom_mensal: e.target.value })} />
            <label className="mb-2 flex items-center gap-2 text-sm">
              <input type="checkbox" checked={pacs.worklist_contratado} onChange={(e) => setPacs({ ...pacs, worklist_contratado: e.target.checked })} />
              Worklist (MWL)
            </label>
            <input className="mb-4 w-full rounded-md border px-3 py-2" placeholder="R$ Worklist / mês" value={pacs.cobranca_worklist_mensal} onChange={(e) => setPacs({ ...pacs, cobranca_worklist_mensal: e.target.value })} />
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setOpenPacs(false)}>Cancelar</button>
              <button type="button" disabled={saving || !lojaAlvoId} className="rounded-md bg-teal-800 px-3 py-2 text-white disabled:opacity-50" onClick={() => void salvarPacs()}>Salvar contrato</button>
            </div>
          </div>
        </div>
      )}

      {openMaq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-5">
            <h2 className="mb-3 text-lg font-semibold">Nova máquina</h2>
            <div className="space-y-2">
              {selectClinica}
              <input className="w-full rounded-md border px-3 py-2" placeholder="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
              <select
                className="w-full rounded-md border px-3 py-2"
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value, cobranca_mensal: PRECO_TIPO[e.target.value] || form.cobranca_mensal })}
              >
                {TIPOS.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
              </select>
              <input className="w-full rounded-md border px-3 py-2 font-mono" placeholder="AE Title (máx. 16)" maxLength={16} value={form.ae_title} onChange={(e) => setForm({ ...form, ae_title: e.target.value.toUpperCase() })} />
              <input className="w-full rounded-md border px-3 py-2" placeholder="Cobrança mensal R$" value={form.cobranca_mensal} onChange={(e) => setForm({ ...form, cobranca_mensal: e.target.value })} />
              <input className="w-full rounded-md border px-3 py-2" placeholder="Fabricante" value={form.fabricante} onChange={(e) => setForm({ ...form, fabricante: e.target.value })} />
              <input className="w-full rounded-md border px-3 py-2" placeholder="Modelo" value={form.modelo} onChange={(e) => setForm({ ...form, modelo: e.target.value })} />
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" onClick={() => setOpenMaq(false)}>Cancelar</button>
              <button type="button" disabled={saving || !lojaAlvoId || !form.nome.trim() || !form.ae_title.trim()} className="rounded-md bg-teal-800 px-3 py-2 text-white disabled:opacity-50" onClick={() => void criarMaquina()}>Cadastrar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
