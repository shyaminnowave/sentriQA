from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework import serializers
from sentriQA.helpers.renders import ResponseInfo
from rest_framework import status
from apps.core.mixins import OptionMixin
from rest_framework.renderers import JSONRenderer

class CustomGenericAPIView(GenericAPIView):

    def get(self, request, *args, **kwargs):
        try:
            response = self.get_serializer(self.get_queryset(), many=True)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Success")
            else:
                return ResponseInfo.error_response(error='error')
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        try:
            response = self.get_serializer(self.get_queryset(), many=True)
            if response.is_valid():
                return ResponseInfo.success_response(data=response.data, message="Success")
            else:
                return ResponseInfo.error_response(error='error')
        except serializers.ValidationError as err:
            return ResponseInfo.error_response(error=str(err))
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)})

class CustomListCreateAPIView(mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              GenericAPIView):
    
    def get(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Success")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomCreateAPIView(mixins.CreateModelMixin, GenericAPIView):

    def post(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomRetrieveAPIVIew(mixins.RetrieveModelMixin, GenericAPIView):

    def get(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Success")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomDestroyAPIView(mixins.DestroyModelMixin, GenericAPIView):

    def delete(self, request, *args, **kwargs):
        try:
            response = self.destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return ResponseInfo.success_response(data="Deleted")
            else:
                return ResponseInfo.error_response(error="Error While Deleted")
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CustomUpdateAPIView(mixins.UpdateModelMixin, GenericAPIView): 
    

    def put(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def patch(self, request, *args, **kwargs):
        try:
            response = super().partial_update(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class CustomRetrieveUpdateAPIView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericAPIView):

    def get(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, *args, **kwargs):
        try:
            response = self.update(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def patch(self, request, *args, **kwargs):
        try:
            response = self.partial_update(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomRetrieveDestroyAPIView(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, GenericAPIView):

    def get(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        try:
            response = self.destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomRetrieveUpdateDestroyAPIView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                                         GenericAPIView):
    
    def get(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.status_code == status.HTTP_200_OK:
                return ResponseInfo.success_response(data=response.data, message="Fetched Successful")
            else:
                return ResponseInfo.error_response(error="Error")
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        try:
            response = self.update(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        try:
            response = self.partial_update(request, *args, **kwargs)
            if response.data:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, *args, **kwargs):
        try:
            response = self.destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return ResponseInfo.success_response(data=response.data, message="Created Successful")
            else:
                return ResponseInfo.error_response(error=response.error)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            return ResponseInfo.error_response(error=default_error)
        except Exception as e:
            return ResponseInfo.error_response(error={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OptionAPIView(OptionMixin, GenericAPIView):

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return ResponseInfo.success_response(
            data=serializer.data if serializer.data else [],
            status_code=status.HTTP_201_CREATED
        )