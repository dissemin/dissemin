from rest_framework import serializers

class NotificationSerializer(serializers.Serializer):
    id = serializers.CharField()
    payload = serializers.JSONField()
    level = serializers.IntegerField()
    tag = serializers.CharField()
