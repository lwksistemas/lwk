from rest_framework import serializers
from .models import Store

class StoreSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Store
        fields = ['id', 'name', 'slug', 'description', 'owner', 'owner_username', 
                  'logo', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['owner', 'created_at', 'updated_at']
