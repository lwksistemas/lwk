"use client";

import { ConvenioFormView } from "./ConvenioFormView";
import { ConveniosListView } from "./ConveniosListView";
import { useConveniosPage } from "./useConveniosPage";

export function ConveniosPageContent() {
  const {
    basePath,
    isNovo,
    convenios,
    loading,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
    novoNome,
    setNovoNome,
    salvando,
    erro,
    voltarLista,
    abrirNovo,
    criarConvenio,
    excluirConvenio,
  } = useConveniosPage();

  if (isNovo) {
    return (
      <ConvenioFormView
        basePath={basePath}
        novoNome={novoNome}
        erro={erro}
        salvando={salvando}
        onNomeChange={setNovoNome}
        onVoltar={voltarLista}
        onSalvar={() => void criarConvenio()}
      />
    );
  }

  return (
    <ConveniosListView
      convenios={convenios}
      loading={loading}
      page={page}
      totalPages={totalPages}
      totalCount={totalCount ?? 0}
      pageSize={pageSize}
      salvando={salvando}
      erro={erro}
      onNova={abrirNovo}
      onExcluir={(c) => void excluirConvenio(c)}
      onPageChange={setPage}
    />
  );
}
