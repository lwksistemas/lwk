"""Testes do flag is_administrador_vinculado no ProfessionalSerializer."""
from unittest import TestCase
from unittest.mock import MagicMock

from clinica_beleza.serializers.professionals import ProfessionalSerializer


class AdminProfessionalSerializerTest(TestCase):
    def _prof(self, pk: int):
        obj = MagicMock()
        obj.id = pk
        return obj

    def test_admin_ids_no_contexto(self):
        prof = self._prof(7)
        serializer = ProfessionalSerializer(context={"admin_professional_ids": {7, 12}})
        self.assertTrue(serializer.get_is_administrador_vinculado(prof))

    def test_nao_admin_quando_fora_do_set(self):
        prof = self._prof(3)
        serializer = ProfessionalSerializer(context={"admin_professional_ids": {7, 12}})
        self.assertFalse(serializer.get_is_administrador_vinculado(prof))

    def test_fallback_owner_professional_id(self):
        prof = self._prof(99)
        serializer = ProfessionalSerializer(context={"owner_professional_id": 99})
        self.assertTrue(serializer.get_is_administrador_vinculado(prof))

    def test_sem_contexto_retorna_false(self):
        prof = self._prof(1)
        serializer = ProfessionalSerializer(context={})
        self.assertFalse(serializer.get_is_administrador_vinculado(prof))
