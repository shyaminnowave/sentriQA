
from rest_framework.response import Response

class OptionMixin:

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.get_queryset(), many=True)
        return Response(serializer.data)