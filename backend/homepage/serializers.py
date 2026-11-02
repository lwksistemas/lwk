from rest_framework import serializers

from core.serializer_mixins import PhoneNormalizationMixin

EFEITOS_HOME = {"typing", "fade", "reveal", "scroll", "slide", "zoom", "nenhuma"}
TRANSICOES_HOME = {"fade", "slide", "zoom", "nenhuma"}
CHAVES_ANIMACAO = ("selo", "titulo", "destaque", "descricao", "botao", "botao2", "secoes")


def _numero(valor, minimo, maximo, padrao):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return padrao
    return max(minimo, min(maximo, numero))


def _item_animacao(bruto):
    bruto = bruto if isinstance(bruto, dict) else {}
    efeito = bruto.get("efeito") if bruto.get("efeito") in EFEITOS_HOME else "nenhuma"
    return {
        "efeito": efeito,
        "ativo": bool(bruto.get("ativo", False)) and efeito != "nenhuma",
        "velocidade": bruto.get("velocidade") if bruto.get("velocidade") in {"lenta", "normal", "rapida"} else "normal",
        "duracao": _numero(bruto.get("duracao"), 200, 3000, 700),
        "atraso": _numero(bruto.get("atraso"), 0, 3000, 0),
        "repetir": bool(bruto.get("repetir", False)),
        "direcao": "vertical" if bruto.get("direcao") == "vertical" else "horizontal",
        "celular": bruto.get("celular") is not False,
    }


def _item_imagem(bruto):
    bruto = bruto if isinstance(bruto, dict) else {}
    transicao = bruto.get("transicao") if bruto.get("transicao") in TRANSICOES_HOME else "fade"
    return {
        "transicao": transicao,
        "ativo": bool(bruto.get("ativo", True)) and transicao != "nenhuma",
        "velocidade": bruto.get("velocidade") if bruto.get("velocidade") in {"lenta", "normal", "rapida"} else "normal",
        "duracao": _numero(bruto.get("duracao"), 200, 3000, 450),
        "atraso": _numero(bruto.get("atraso"), 0, 3000, 0),
        "celular": bruto.get("celular") is not False,
    }


def _dispositivo(bruto):
    bruto = bruto if isinstance(bruto, dict) else {}
    return {chave: _item_animacao(bruto.get(chave)) for chave in CHAVES_ANIMACAO} | {"imagens": _item_imagem(bruto.get("imagens"))}


def _animacoes_limpas(bruto):
    computador = _dispositivo(bruto.get("computador"))
    igual = bruto.get("igual_celular") is not False
    return {
        "igual_celular": igual,
        "computador": computador,
        "celular": computador if igual else _dispositivo(bruto.get("celular")),
    }

from .models import (
    EmpresaConfig,
    Funcionalidade,
    HeroSection,
    ItemMenu,
    ModuloSistema,
    PaginaSite,
    SolicitacaoContato,
    WhyUsBenefit,
)


class HeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = [
            "id",
            "titulo",
            "subtitulo",
            "selo",
            "botao_texto",
            "botao_url",
            "botao_principal_ativo",
            "botao_secundario_texto",
            "botao_secundario_url",
            "botao_secundario_ativo",
            "intervalo_carrossel",
            "titulo_destaque",
            "fonte_familia",
            "fonte_tamanho",
            "rotulos_botoes",
            "animacoes",
            "ordem",
            "ativo",
        ]
        extra_kwargs = {
            "botao_principal_ativo": {"required": False, "default": True},
            "titulo_destaque": {"required": False, "allow_blank": True},
            "fonte_familia": {"required": False},
            "fonte_tamanho": {"required": False},
            "rotulos_botoes": {"required": False},
            "animacoes": {"required": False},
        }

    def validate_rotulos_botoes(self, value):
        if not value:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("Informe os nomes dos botões.")
        limpo = {}
        for chave, texto in value.items():
            if isinstance(chave, str) and isinstance(texto, str) and texto.strip():
                limpo[chave[:40]] = texto.strip()[:80]
        return limpo

    def validate_animacoes(self, value):
        if not value:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("Informe as animações da homepage.")
        return _animacoes_limpas(value)

    def update(self, instance, validated_data):
        if validated_data.get("animacoes") and instance.animacoes:
            from django.utils import timezone

            historico = list(instance.animacoes_historico or [])
            historico.insert(0, {"salvo_em": timezone.now().isoformat(), "animacoes": instance.animacoes})
            instance.animacoes_historico = historico[:8]
        return super().update(instance, validated_data)


class HeroAdminSerializer(HeroSerializer):
    class Meta(HeroSerializer.Meta):
        fields = [*HeroSerializer.Meta.fields, "animacoes_historico"]
        read_only_fields = ["animacoes_historico"]


class FuncionalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionalidade
        fields = ["id", "titulo", "descricao", "icone", "link", "imagem", "ordem", "ativo"]
        extra_kwargs = {
            "icone": {"allow_blank": True, "required": False},
            "link": {"allow_blank": True, "required": False},
            "imagem": {"required": False, "allow_blank": True, "allow_null": True},
        }


class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuloSistema
        fields = ["id", "nome", "descricao", "slug", "icone", "imagem", "ordem", "ativo"]
        extra_kwargs = {
            "imagem": {"required": False, "allow_blank": True, "allow_null": True},
        }

    def validate_slug(self, value):
        """Valida se o slug é único (exceto para o próprio registro em edição)"""
        if not value:
            return value

        # Verifica se já existe outro módulo com o mesmo slug
        queryset = ModuloSistema.objects.filter(slug=value)

        # Se estamos editando, excluir o próprio registro da verificação
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(f'Já existe um módulo com o slug "{value}". Escolha outro.')

        return value


class WhyUsBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhyUsBenefit
        fields = ["id", "titulo", "descricao", "icone", "ordem", "ativo"]
        extra_kwargs = {
            "descricao": {"required": False, "allow_blank": True},
            "icone": {"required": False, "allow_blank": True, "default": "✓"},
        }


class EmpresaConfigSerializer(PhoneNormalizationMixin, serializers.ModelSerializer):
    phone_fields = ["telefone_whatsapp"]

    class Meta:
        model = EmpresaConfig
        fields = ["id", "nome_empresa", "cnpj", "endereco", "telefone_whatsapp", "mensagem_whatsapp", "email_contato", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "cnpj": {"required": False, "allow_blank": True},
            "endereco": {"required": False, "allow_blank": True},
            "telefone_whatsapp": {"required": False, "allow_blank": True},
            "mensagem_whatsapp": {"required": False, "allow_blank": True},
            "email_contato": {"required": False, "allow_blank": True},
        }


class ItemMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemMenu
        fields = ["id", "grupo", "rotulo", "url", "ordem", "ativo"]


class PaginaSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaginaSite
        fields = ["id", "slug", "titulo", "resumo", "corpo", "itens", "mensagem_whatsapp", "imagem", "ativo"]
        extra_kwargs = {
            "imagem": {"required": False, "allow_blank": True},
        }


PRODUTOS_CONTATO = {"crm-vendas", "clinicas-estetica", "personalizados", "outros", "geral"}


class SolicitacaoContatoSerializer(serializers.ModelSerializer):
    aceite_lgpd = serializers.BooleanField(write_only=True)

    class Meta:
        model = SolicitacaoContato
        fields = ["nome", "empresa", "whatsapp", "produto", "mensagem", "origem", "aceite_lgpd"]
        extra_kwargs = {
            "empresa": {"required": False, "allow_blank": True},
            "origem": {"required": False},
        }

    def validate_aceite_lgpd(self, value):
        if value is not True:
            raise serializers.ValidationError("É preciso aceitar o aviso de privacidade.")
        return value

    def validate_produto(self, value):
        if value not in PRODUTOS_CONTATO:
            raise serializers.ValidationError("Escolha o produto de interesse.")
        return value

    def validate_whatsapp(self, value):
        digitos = "".join(ch for ch in (value or "") if ch.isdigit())
        if len(digitos) < 10 or len(digitos) > 13:
            raise serializers.ValidationError("Informe um WhatsApp com DDD.")
        return digitos

    def create(self, validated_data):
        validated_data.pop("aceite_lgpd", None)
        return super().create(validated_data)
