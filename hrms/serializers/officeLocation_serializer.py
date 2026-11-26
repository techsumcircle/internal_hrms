from hrms.models import OfficeLocation
from rest_framework import serializers

class OfficeLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficeLocation
        fields = [
            'id',
            'name',
            'latitude',
            'longitude',
            'radius_meters',
            'is_active',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']