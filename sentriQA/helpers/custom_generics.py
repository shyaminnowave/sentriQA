import json
import traceback
from typing import Any
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework import serializers

from apps.core.apis.serializers import TestplanSessionSerializer
from sentriQA.helpers.renders import ResponseInfo
from rest_framework import status
from rest_framework.views import Response
from apps.core.mixins import OptionMixin


class CustomGenericAPIView(GenericAPIView):

    def get(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = self.get_serializer(self.get_queryset(), many=True)
            if response.data:
                return handler._success_response(data=response.data, message="Success")
            else:
                return handler._error_response(error='error')
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(error=default_error)
        except Exception as e:
            return handler._error_response(error='error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomListCreateAPIView(mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              GenericAPIView):
    
    def get(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = super().list(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Success")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(error={"error": str(e)})
        
    def post(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = super().create(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)})


class CustomCreateAPIView(mixins.CreateModelMixin, GenericAPIView):

    def post(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = super().create(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)})


class CustomRetriveAPIVIew(mixins.RetrieveModelMixin, GenericAPIView): 

    def get(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Success")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)})


class CustomDestroyAPIView(mixins.DestroyModelMixin, GenericAPIView):

    def delete(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = self.destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return handler._success_response(data="Deleted")
            else:
                return handler._error_response(error="Error While Deleted")
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)})    
        

class CustomUpdateAPIView(mixins.UpdateModelMixin, GenericAPIView): 
    

    def put(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = super().update(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def patch(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = super().partial_update(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class CustomRetrieveUpdateAPIView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericAPIView):

    def get(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = self.update(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def patch(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = self.partial_update(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomRetrieveDestroyAPIView(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, GenericAPIView):

    def get(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = self.destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomRetrieveUpdateDestroyAPIView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                                         GenericAPIView):
    
    def get(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = self.update(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = self.partial_update(request, *args, **kwargs)
            if response.data:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, *args, **kwargs):
        handler = ResponseInfo()
        try:
            response = self.destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return handler._success_response(data=response.data, message="Created Successful")
            else:
                return handler._error_response(data=response.error)    
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return handler._error_response(data=default_error)
        except Exception as e:
            return handler._error_response(data={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OptionAPIView(OptionMixin, GenericAPIView):

    def get(self, request, *args, **kwargs):
        handler = ResponseInfo()
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return handler._success_response(
            data=serializer.data if serializer.data else [],
            status=status.HTTP_201_CREATED
        )