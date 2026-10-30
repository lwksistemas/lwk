"""XML de NF-e enviado pelo usuário não pode expandir entidades."""
from unittest import TestCase

from clinica_beleza.estoque_xml_import_service import parse_nfe_xml

BOMBA = b"""<?xml version="1.0"?>
<!DOCTYPE bomb [
  <!ENTITY a "aaaaaaaaaa">
  <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">
]>
<nfeProc><NFe><infNFe>&b;</infNFe></NFe></nfeProc>
"""


class NfeXmlDefusedTest(TestCase):
    def test_recusa_expansao_de_entidade(self):
        with self.assertRaises(ValueError):
            parse_nfe_xml(BOMBA)
