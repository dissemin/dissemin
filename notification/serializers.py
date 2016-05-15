from rest_framework import serializers

class NotificationSerializer(serializers.Serializer):
    id = serializers.CharField()
    notification = serializers.JSONField()
    level = serializers.IntegerField()
