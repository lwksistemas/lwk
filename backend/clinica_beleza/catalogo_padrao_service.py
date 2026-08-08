"""Helpers compartilhados para catálogos com flag is_padrao (locais, nomes agenda)."""


def garantir_primeiro_padrao(model, instance) -> None:
    """Se a loja não tem nenhum padrão ativo, marca a instância como padrão."""
    tem_padrao = model.objects.using(instance._state.db).filter(
        loja_id=instance.loja_id,
        is_padrao=True,
        is_active=True,
    ).exists()
    if not tem_padrao:
        instance.is_padrao = True
        instance.save(update_fields=["is_padrao"])


def exclusivizar_padrao(model, instance) -> None:
    """Se a instância é padrão, desmarca os demais da mesma loja."""
    if not instance.is_padrao:
        return
    model.objects.using(instance._state.db).filter(
        loja_id=instance.loja_id,
        is_padrao=True,
    ).exclude(pk=instance.pk).update(is_padrao=False)
