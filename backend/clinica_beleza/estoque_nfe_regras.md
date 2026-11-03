# Importação de NF-e no estoque da clínica

Leitura de saldo. Nenhuma destas regras reescreve `quantidade_atual`, movimentação antiga ou saldo que já existia sem lote.

## Saldos

- Total é `quantidade_atual`.
- Saldo anterior sem lote é o total menos a soma dos lotes com quantidade maior que zero. Ele não recebe código de lote.
- Utilizável é o total menos a quantidade que está só em lote vencido. O saldo anterior entra nessa conta. Produto inativo tem utilizável zero.
- O cadastro mostra sempre as três linhas: Total, utilizável e saldo anterior sem lote, mesmo quando não há lote novo.
- Quando os lotes válidos acabam, a saída seguinte diminui o saldo anterior. Lote vencido permanece e não entra no utilizável.
- Saída maior que o utilizável é recusada por inteiro. Ajuste de inventário não percorre os lotes e pode regularizar o saldo anterior no futuro.

## Saída (FEFO)

1. Lote com validade ainda não vencida, o que vence antes.
2. Lote sem validade.
3. Saldo anterior sem lote, que não é uma linha de lote.
4. Lote vencido não é baixado.

## Entrada da nota

- Um produto interno pode ter vários fornecedores, cada um com o próprio código e último custo convertido.
- Vínculo por código do fornecedor ou GTIN único. Nome só igual entra direto. Nome parecido ou código e GTIN apontando produtos diferentes pedem escolha. Não vincula sozinho nesse caso.
- Itens idênticos são o mesmo GTIN ou o mesmo nome normalizado. A decisão de vincular, cadastrar ou ignorar pode ser copiada. Quantidade, lote e validade de cada linha permanecem.
- Caixa vira unidade quando a quantidade tributária dividida pela comercial é inteira de 1 a 1000. Quilo continua quilo.
- Custo da unidade de estoque é o valor comercial líquido (produto, ou unitário vezes quantidade, menos desconto, mais frete, seguro e outras despesas) dividido pelo fator.
- Confirmação é transacional. Nota já importada na mesma loja não entra de novo. Item sem decisão bloqueia. Produto que exige lote sem lote ou validade bloqueia. Falha desfaz a nota inteira.
- Série e custo total da compra são calculados na leitura, a partir da chave e do custo unitário.

## Testes

Arquivo `clinica_beleza/tests/test_estoque_nfe_vinculo.py`. Não gravam banco.

Em 3 de novembro de 2026 o serviço da clínica rodou 24 testes deste arquivo, no commit `3c56b10fa`, com resultado OK. A publicação seguinte acrescenta `test_quando_os_lotes_novos_acabam_o_saldo_antigo_continua_utilizavel`.

- `test_caixa_com_cinco_frascos`
- `test_mesma_unidade_nao_converte`
- `test_gtin_vazio_da_nota`
- `test_codigo_do_fornecedor_vincula_sem_perguntar`
- `test_gtin_de_outro_fornecedor_acha_o_mesmo_produto`
- `test_nome_parecido_pede_confirmacao`
- `test_sem_correspondencia_cadastra`
- `test_caixa_de_262_vira_52_40_por_frasco`
- `test_desconto_e_frete_entram_no_custo`
- `test_quilo_nao_vira_unidade`
- `test_codigo_e_gtin_conflitantes_pedem_escolha`
- `test_nome_parecido_nao_e_o_mesmo_item`
- `test_gtins_diferentes_nao_repetem_juntos`
- `test_exige_lote_sem_validade_bloqueia`
- `test_saida_consome_o_lote_que_vence_antes`
- `test_saldo_antigo_fica_fora_dos_lotes_depois_da_saida`
- `test_quando_os_lotes_novos_acabam_o_saldo_antigo_continua_utilizavel`
- `test_vencido_e_sem_validade_nao_furam_a_fila`
- `test_tres_fornecedores_um_produto_pelo_gtin`
- `test_linhas_iguais_guardam_lotes_diferentes`
- `test_serie_e_total_da_caixa`
- `test_decisao_pendente_nao_libera_a_nota`
- `test_confirmacao_esta_dentro_de_uma_transacao`
- `test_repetido_na_nota_nao_cadastra_calado`
- `test_xml_le_gtin_fator_e_lote`

A tela da conferência também está em `frontend/lib/estoque-importar-xml-utils.test.ts`.
