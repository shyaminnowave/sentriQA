import json
import traceback
from typing import Any
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework import serializers
from sentriQA.helpers.renders import ResponseInfo
from rest_framework import status
from rest_framework.views import Response
from apps.core.mixins import OptionMixin


class CustomGenericsAPIView(GenericAPIView):

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super(CustomGenericsAPIView, self).__init__(**kwargs)


    # def _success_response(self, data: Any, message: str = "Success", status_code: int = status.HTTP_200_OK) -> Response:
    #     self.response_format['status'] = True
    #     self.response_format['status_code'] = status_code
    #     self.response_format['data'] = data
    #     self.response_format['message'] = message
    #     return Response(self.response_format, status=status_code)
    
    # def _error_response(self, error: Any, message: str = "Error", status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    #     self.response_format['status'] = False
    #     self.response_format['status_code'] = status_code
    #     self.response_format['data'] = error
    #     self.response_format['message'] = message
    #     return Response(self.response_format, status=status_code)
        

class CustomListCreateAPIView(mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              GenericAPIView):

    def __init__(self, **kwargs: Any) -> None:
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            if response.data:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = response.data
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            if response.status_code == status.HTTP_201_CREATED:
                return Response({
                    "status": True,
                    "status_code": status.HTTP_201_CREATED,
                    "data": response.data,
                    "message": "Success"
                }, status.HTTP_201_CREATED)
            else:
                return Response({
                    "status": False,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "data": response.errors,
                    "message": "Success"
                }, status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as e:
            default_error = {field: message[0] if isinstance(message, list) else message for field, message in
                             e.detail.items()}
            return Response({
                "status": False,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "data": default_error,
                "message": "Success"
            }, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "data": str(e),
                "message": "Success"
            }, status.HTTP_400_BAD_REQUEST)


class CustomCreateAPIView(mixins.CreateModelMixin, GenericAPIView):

    def __init__(self, **kwargs: Any) -> None:
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            if response.status_code == status.HTTP_201_CREATED:
                self.response_format['status'] = True
                self.response_format['status_code'] = response.status_code
                self.response_format['data'] = response.data
                self.response_format['message'] = "TestCase Script Added Success"
                return Response(self.response_format, status=status.HTTP_201_CREATED)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = response.status_code
                self.response_format['data'] = 'Error'
                self.response_format['message'] = "Error"
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)


class CustomRetriveAPIVIew(mixins.RetrieveModelMixin, GenericAPIView): 

    def __init__(self, **kwargs: Any) -> None:
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.data:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = response.data
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomDestroyAPIView(mixins.DestroyModelMixin, GenericAPIView):

    def __init__(self, **kwargs: Any) -> None:
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            response = self.destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = "Deleted"
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomUpdateAPIView(mixins.UpdateModelMixin, GenericAPIView): 
    
    def __init__(self, **kwargs: Any) -> None:
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def put(self, request, *args, **kwargs):
        try:
            response = self.update(request, *args, **kwargs)
            if response.data:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = response.data
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def patch(self, request, *args, **kwargs):
        try:
            response = self.partial_update(request, *args, **kwargs)
            if response.data:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = response.data
                self.response_format['message'] = "Success"
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class CustomRetrieveUpdateAPIView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericAPIView):
    
    def __init__(self, **kwargs: Any) -> None:
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.data:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = response.data
                self.response_format['message'] = "Success"
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, *args, **kwargs):
        try:
            response = self.update(request, *args, **kwargs)
            if response.data:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = response.data
                self.response_format['message'] = "Success"
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def patch(self, request, *args, **kwargs):
        try:
            response = self.partial_update(request, *args, **kwargs)
            if response.data:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = response.data
                self.response_format['message'] = "Success"
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomRetrieveDestroyAPIView(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, GenericAPIView):
    
    def __init__(self, **kwargs: Any) -> None:
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.data:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = response.data
                self.response_format['message'] = "Success"
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, *args, **kwargs):
        try:
            response = self.destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = "Deleted"
                self.response_format['message'] = "Success"
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomRetrieveUpdateDestroyAPIView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                                         GenericAPIView):
    
    def __init__(self, **kwargs: Any) -> None:
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.data:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = response.data
                self.response_format['message'] = "Success"
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        try:
            response = self.update(request, *args, **kwargs)
            if response.data:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = response.data
                self.response_format['message'] = "Success"
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        try:
            response = self.partial_update(request, *args, **kwargs)
            if response.data:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = response.data
                self.response_format['message'] = "Success"
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, *args, **kwargs):
        try:
            response = self.destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = "Deleted"
                self.response_format['message'] = "Success"
                return Response(self.response_format, status=status.HTTP_200_OK)
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = response.errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as err:
            default_error = {key: value[0] if isinstance(value, list) else value for key, value in err.detail.items()}
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['data'] = 'Error'
            self.response_format['message'] = default_error
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.response_format['message'] = {"error": str(e)}
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OptionAPIView(OptionMixin, GenericAPIView):

    def __init__(self, **kwargs: Any) -> None:
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({
            "status": True,
            "status_code": status.HTTP_200_OK,
            "data": serializer.data if serializer.data else [],
            "message": "Success"
        }, status.HTTP_201_CREATED)