from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from core.upload_validation import validate_pdf_upload, validate_xml_upload


class UploadValidationTests(SimpleTestCase):
    def test_pdf_magic_bytes(self):
        f = SimpleUploadedFile('doc.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        ok, _ = validate_pdf_upload(f)
        self.assertTrue(ok)

    def test_pdf_rejects_non_pdf(self):
        f = SimpleUploadedFile('bad.pdf', b'not a pdf', content_type='application/pdf')
        ok, msg = validate_pdf_upload(f)
        self.assertFalse(ok)
        self.assertIn('conteúdo', msg.lower())

    def test_xml_upload(self):
        f = SimpleUploadedFile('nfe.xml', b'<?xml version="1.0"?><nfe/>', content_type='text/xml')
        ok, _ = validate_xml_upload(f)
        self.assertTrue(ok)
