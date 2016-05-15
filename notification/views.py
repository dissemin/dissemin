from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view, detail_route
from rest_framework.response import Response

from django.contrib.auth.decorators import login_required

from .serializers import NotificationSerializer
from .backends.exceptions import NotificationDoesNotExist

from .api import get_backend_class

class InboxViewSet(viewsets.ViewSet):
    """
    Provides `list` and `detail` actions.
    And a POST endpoint to `read` inbox messages.
    """

    def list(self, request):
        BackendClass = get_backend_class()
        backend = BackendClass()
        notifications = backend.inbox_list(request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        BackendClass = get_backend_class()
        backend = BackendClass()

        try:
            notification = backend.inbox_get(request.user, pk)
        except NotificationDoesNotExist as e:
            return Response(e.message, status='404')
        else:
            serializer = NotificationSerializer(notification)
            return Response(serializer.data)

    @detail_route(methods=['POST'])
    def read(self, request, pk=None):
        """
        Mark the message as read.
        """
        BackendClass = get_backend_class()
        backend = BackendClass()

        try:
            backend.inbox_delete(request.user, pk)
        except NotificationDoesNotExist as e:
            return Response(e.message, status='404')
        else:
            return Response({
                'status': 'Message marked as read successfully.'
            })
