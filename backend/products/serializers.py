from rest_framework import serializers

from core.serializer_mixins import UpperCaseNormalizationMixin

from .models import Product


class ProductSerializer(UpperCaseNormalizationMixin, serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)
    uppercase_fields = ["name"]

    class Meta:
        model = Product
        fields = ["id", "store", "store_name", "name", "slug", "description",
                  "price", "stock", "image", "is_active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
