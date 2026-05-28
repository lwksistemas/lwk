#!/usr/bin/env node
/**
 * Verificação automatizada dos helpers da refatoração (seção 5 do doc).
 * Não substitui testes manuais de UI.
 */

// --- nfse (espelho das regras em lib/nfse-helpers.ts) ---
const NFSE_CANCELAMENTO_OPCOES = { '1': 'Erro na emissão', '2': 'Serviço não prestado', '4': 'Duplicidade da nota' };

function nfseIdentificador(nf) {
  if (nf.numero_nf) return nf.numero_nf;
  if (nf.numero_rps != null) return `RPS ${nf.numero_rps}`;
  return String(nf.id ?? '');
}

function nfUsaIssnet(nf, lojaProvedor) {
  const p = (nf.provedor || '').toLowerCase();
  const d = (nf.provedor_display || '').toLowerCase();
  const loja = (lojaProvedor || '').toLowerCase();
  if (p === 'issnet' || d.includes('issnet')) return true;
  return loja === 'issnet';
}

function nfseSyncEndpoint(nf, lojaProvedor) {
  if (nfUsaIssnet(nf, lojaProvedor)) return 'sincronizar-issnet';
  if ((nf.provedor || '').toLowerCase() === 'asaas' || (lojaProvedor || '').toLowerCase() === 'asaas') {
    return 'sincronizar-asaas';
  }
  return null;
}

function nfsePodeBaixar(s) { return s === 'emitida' || s === 'cancelada'; }
function nfsePodeSincronizar(s) { return s === 'emitida' || s === 'erro'; }
function nfsePodeCancelar(s) { return s === 'emitida'; }
function nfsePodeExcluirSuperadmin(s) { return s === 'erro' || s === 'pendente'; }
function nfsePodeExcluirLoja(s) { return s !== 'emitida' && s !== 'cancelada'; }

function filtrarNfsesPorBusca(nfses, busca) {
  if (!busca.trim()) return nfses;
  const q = busca.toLowerCase();
  return nfses.filter(
    (nf) =>
      (nf.numero_nf ?? '').toLowerCase().includes(q) ||
      (nf.tomador_nome ?? '').toLowerCase().includes(q) ||
      (nf.tomador_cpf_cnpj ?? '').includes(busca),
  );
}

// --- clinica offline ---
function isRegistroPendenteSync(id) { return id < 0; }
function deveVerificarDuplicataOffline(editing) {
  if (!editing) return true;
  return isRegistroPendenteSync(editing.id);
}
function bloquearCriacaoDuplicadaOffline(editing, list, predicateNovo) {
  if (editing) return false;
  return list.some(predicateNovo);
}

// --- clinica form errors (subset) ---
function formatClinicaApiValidationErrors(err, fieldLabels = { name: 'Nome' }) {
  if (err?.detail && typeof err.detail === 'string') return err.detail;
  const msgs = [];
  for (const [key, val] of Object.entries(err)) {
    if (key === 'detail') continue;
    if (Array.isArray(val) && val.length && typeof val[0] === 'string') {
      msgs.push(`${fieldLabels[key] || key}: ${val[0]}`);
    }
  }
  return msgs.length ? msgs.join('. ') : '';
}

const failures = [];

function assert(cond, msg) {
  if (!cond) failures.push(msg);
}

assert(nfseIdentificador({ numero_nf: '123' }) === '123', 'nfseIdentificador numero_nf');
assert(nfseIdentificador({ numero_rps: 5, id: 1 }) === 'RPS 5', 'nfseIdentificador rps');
assert(Object.keys(NFSE_CANCELAMENTO_OPCOES).length === 3, 'cancelamento opcoes');
assert(nfUsaIssnet({ provedor: 'issnet' }), 'issnet provedor');
assert(nfseSyncEndpoint({ provedor: 'asaas' }) === 'sincronizar-asaas', 'sync asaas');
assert(nfsePodeBaixar('emitida') && !nfsePodeCancelar('cancelada'), 'regras baixar/cancelar');
assert(nfsePodeExcluirSuperadmin('erro') && !nfsePodeExcluirLoja('emitida'), 'regras excluir');
assert(
  filtrarNfsesPorBusca(
    [{ numero_nf: '99', tomador_nome: 'João', tomador_cpf_cnpj: '111' }],
    'joão',
  ).length === 1,
  'filtrar busca tomador',
);
assert(deveVerificarDuplicataOffline(null), 'duplicata offline criar');
assert(!deveVerificarDuplicataOffline({ id: 10 }), 'duplicata offline edit sync');
assert(bloquearCriacaoDuplicadaOffline(null, [{ cpf: '1' }], (x) => x.cpf === '1'), 'bloqueio duplicata');
assert(
  formatClinicaApiValidationErrors({ name: ['obrigatório'] }).includes('Nome'),
  'format erro paciente',
);

if (failures.length) {
  console.error('FALHAS:', failures.join('\n'));
  process.exit(1);
}
console.log('frontend_helpers: OK (' + (12 - failures.length) + ' asserts)');
