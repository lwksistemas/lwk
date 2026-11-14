"""Chave, QR Code e XML da NFC-e, sem banco e sem SEFAZ."""
import unittest
from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from lxml import etree

from clinica_beleza.nfce.chave import digito_chave, montar_chave, url_qrcode
from clinica_beleza.nfce.xml_nfce import assinar_raiz, envelopar, montar_nfe


def _dados():
    return {
        "homologacao": True,
        "chave": "352611373027430001266500100000000111234567890",
        "codigo": "12345678",
        "serie": 1,
        "numero": 1,
        "quando": "2026-11-14T16:50:00-03:00",
        "municipio": "3540903",
        "documento": "37302743000126",
        "nome": "Clinica Harmonis",
        "logradouro": "Rua Sao Martinho",
        "numero_endereco": "100",
        "bairro": "Centro",
        "cidade": "Pradopolis",
        "cep": "14850000",
        "ie": "123456789012",
        "simples": True,
        "cpf": "",
        "itens": [{
            "codigo": 10,
            "nome": "Protetor",
            "ncm": "33049910",
            "unidade": "unidade",
            "quantidade": "1",
            "preco": "25.00",
            "bruto": "25.00",
            "desconto": "0",
            "liquido": "25.00",
            "icms": "0",
            "pis": "0",
            "cofins": "0",
        }],
        "bruto": "25.00",
        "desconto": "0",
        "liquido": "25.00",
        "base_icms": "0",
        "icms": "0",
        "pis": "0",
        "cofins": "0",
        "tpag": "01",
        "aliquota_icms": "18.00",
        "qrcode": "https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode?p=teste",
    }


class ChaveNfceTest(unittest.TestCase):
    def test_digito_e_tamanho(self):
        base = "35" + "2611" + "37302743000126" + "65" + "001" + "000000001" + "1" + "12345678"
        self.assertEqual(len(base), 43)
        chave = montar_chave(
            cnpj="37.302.743/0001-26",
            ano_mes="2611",
            serie=1,
            numero=1,
            codigo="12345678",
        )
        self.assertEqual(len(chave), 44)
        self.assertEqual(chave[-1], digito_chave(chave[:-1]))
        self.assertTrue(chave.startswith(base[:43]))

    def test_qr_carrega_o_csc_so_no_hash(self):
        chave = "3" * 44
        url = url_qrcode(chave=chave, homologacao=True, id_csc="000001", csc="SEGREDO")
        self.assertIn(chave, url)
        self.assertNotIn("SEGREDO", url)
        self.assertTrue(url.startswith("https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode?p="))


class XmlNfceTest(unittest.TestCase):
    def test_simples_na_homologacao(self):
        xml = envelopar(montar_nfe(_dados()))
        self.assertIn("<mod>65</mod>", xml)
        self.assertIn("<CSOSN>102</CSOSN>", xml)
        self.assertIn("NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL", xml)
        self.assertNotIn("<ICMS00>", xml)

    def test_assinatura_fica_fora_do_inf_nfe(self):
        chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "NFC-e teste")])
        certificado = (
            x509.CertificateBuilder()
            .subject_name(nome)
            .issuer_name(nome)
            .public_key(chave.public_key())
            .serial_number(1)
            .not_valid_before(datetime(2026, 1, 1, tzinfo=timezone.utc))
            .not_valid_after(datetime(2027, 1, 1, tzinfo=timezone.utc))
            .sign(chave, hashes.SHA256())
        )
        key_pem = chave.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        cert_pem = certificado.public_bytes(serialization.Encoding.PEM)
        assinado = assinar_raiz(montar_nfe(_dados()), key_pem, cert_pem)
        filhos = [no.tag.split("}")[-1] for no in assinado]
        self.assertEqual(filhos, ["infNFe", "infNFeSupl", "Signature"])
        inf = assinado[0]
        self.assertFalse(any(no.tag.split("}")[-1] == "Signature" for no in inf))
        self.assertIsNone(etree.fromstring(etree.tostring(assinado)).find(".//{http://www.w3.org/2000/09/xmldsig#}KeyValue"))


if __name__ == "__main__":
    unittest.main()
