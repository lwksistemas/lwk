"""Validação de anamnese — peso/altura vazios devem virar null."""
from unittest import TestCase

from clinica_beleza.serializers.patients import PatientAnamneseSerializer


class PatientAnamneseSerializerTest(TestCase):
    def test_peso_altura_vazios_aceitos(self):
        serializer = PatientAnamneseSerializer()
        self.assertIsNone(serializer.validate_peso(''))
        self.assertIsNone(serializer.validate_altura(''))
        self.assertIsNone(serializer.validate_peso(None))
        self.assertIsNone(serializer.validate_altura(None))

    def test_peso_altura_numericos_preservados(self):
        serializer = PatientAnamneseSerializer()
        self.assertEqual(serializer.validate_peso('72.5'), '72.5')
        self.assertEqual(serializer.validate_altura('1.75'), '1.75')
