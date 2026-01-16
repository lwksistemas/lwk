from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'store', 'store_name', 'name', 'slug', 'description', 
                  'price', 'stock', 'image', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
