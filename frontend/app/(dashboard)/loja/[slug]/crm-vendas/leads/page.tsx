'use client';

import dynamic from 'next/dynamic';
import { STATUS_LEAD_OPCOES } from '@/constants/crm';
import { Plus, Download } from 'lucide-react';
import LeadsTable from '@/components/crm-vendas/LeadsTable';
import CrmPaginationBar from '@/components/crm-vendas/CrmPaginationBar';
import { useCrmLeadsPage } from '@/hooks/crm-vendas/useCrmLeadsPage';

const ModalLeadVer = dynamic(() => import('@/components/crm-vendas/modals/ModalLeadVer'), { ssr: false });
const ModalLeadForm = dynamic(() => import('@/components/crm-vendas/modals/ModalLeadForm'), { ssr: false });
const ModalLeadExcluir = dynamic(() => import('@/components/crm-vendas/modals/ModalLeadExcluir'), { ssr: false });
const ModalLeadMudarStatus = dynamic(() => import('@/components/crm-vendas/modals/ModalLeadMudarStatus'), { ssr: false });

export default function CrmVendasLeadsPage() {
  const {
    slug,
    leads,
    page,
    setPage,
    totalCount,
    totalPages,
    loading,
    error,
    leadVer,
    setLeadVer,
    leadEditar,
    setLeadEditar,
    leadExcluir,
    setLeadExcluir,
    leadMudarStatus,
    setLeadMudarStatus,
    novoStatus,
    setNovoStatus,
    salvandoEdicao,
    salvandoStatus,
    excluindo,
    formErro,
    setFormErro,
    form,
    setForm,
    colunasLeadsVisiveis,
    origensAtivas,
    origemLabel,
    statusLabel,
    formatarDataLead,
    handleEditarLead,
    handleSalvarEdicao,
    confirmarExcluir,
    handleMudarStatus,
    salvarNovoStatus,
    exportLeadsCsv,
    leadsPageSize,
  } = useCrmLeadsPage();

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-white">Leads</h1>
        <div className="rounded-xl bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-white">Leads</h1>
        <div className="flex items-center gap-2">
          {leads.length > 0 && (
            <button
              type="button"
              onClick={() => exportLeadsCsv(leads)}
              className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 px-3 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 font-medium transition text-sm inline-flex items-center gap-2"
            >
              <Download size={16} />
              Exportar CSV
            </button>
          )}
          <a
            href={`/loja/${slug}/crm-vendas/leads/novo`}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition text-sm inline-flex items-center gap-2"
          >
            <Plus size={18} />
            Novo Lead
          </a>
        </div>
      </div>

      <LeadsTable
        leads={leads}
        loading={loading}
        colunas={colunasLeadsVisiveis()}
        onVerLead={setLeadVer}
        onEditarLead={handleEditarLead}
        onExcluirLead={setLeadExcluir}
        onMudarStatus={handleMudarStatus}
      />

      <CrmPaginationBar
        page={page}
        totalPages={totalPages}
        totalCount={totalCount}
        pageSize={leadsPageSize}
        loading={loading}
        itemLabel="leads"
        onPageChange={setPage}
      />

      {leadVer && (
        <ModalLeadVer
          lead={leadVer}
          slug={slug}
          origemLabel={origemLabel}
          statusLabel={statusLabel}
          formatarData={formatarDataLead}
          onClose={() => setLeadVer(null)}
          onEditar={(lead) => {
            setLeadVer(null);
            handleEditarLead(lead);
          }}
        />
      )}

      {leadEditar && (
        <ModalLeadForm
          title="Editar lead"
          form={form}
          formErro={formErro}
          enviando={salvandoEdicao}
          origensAtivas={origensAtivas}
          statusOpcoes={[...STATUS_LEAD_OPCOES]}
          onFormChange={(updater) => setForm(updater)}
          onSubmit={handleSalvarEdicao}
          onClose={() => !salvandoEdicao && setLeadEditar(null)}
        />
      )}

      {leadExcluir && (
        <ModalLeadExcluir
          lead={leadExcluir}
          excluindo={excluindo}
          onConfirm={confirmarExcluir}
          onClose={() => !excluindo && setLeadExcluir(null)}
        />
      )}

      {leadMudarStatus && (
        <ModalLeadMudarStatus
          lead={leadMudarStatus}
          novoStatus={novoStatus}
          formErro={formErro}
          enviando={salvandoStatus}
          statusOpcoes={[...STATUS_LEAD_OPCOES]}
          onNovoStatusChange={setNovoStatus}
          onSalvar={salvarNovoStatus}
          onClose={() => {
            if (!salvandoStatus) setLeadMudarStatus(null);
            setFormErro(null);
          }}
        />
      )}
    </div>
  );
}
