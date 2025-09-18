from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework import status
from apps.account.utils import get_token_for_user
from apps.account.apis.serializers import LoginSerializer, AccountSerializer
from django.contrib.auth import authenticate, login, logout


class LoginAPIView(APIView):

    def __init__(self, **kwargs):
        self.response_format = {}
        super().__init__(**kwargs)

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                default_errors = {field: error[0] for field, error in serializer.errors.items()}
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['message'] = default_errors
                return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

            user_cred = self._perform_login(request, email=serializer.validated_data.get('email', None),
                                            password=serializer.validated_data.get('password', None))

            if user_cred is not None:
                self.response_format['status'] = True
                self.response_format['status_code'] = status.HTTP_200_OK
                self.response_format['data'] = user_cred
                self.response_format['message'] = "User Login Successfull"
                response = Response(self.response_format,
                                    status=status.HTTP_200_OK)
                return response
            else:
                self.response_format['status'] = False
                self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
                self.response_format['data'] = user_cred
                self.response_format['message'] = {
                    "error": "Email or Password Not Match, Please enter the Correct Details"
                }
                return Response(self.response_format,
                                status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            self.response_format['status'] = False
            self.response_format['status_code'] = status.HTTP_400_BAD_REQUEST
            self.response_format['message'] = str(e)
            return Response({'success': False, 'error': "Please Check the login credentials"},
                            status=status.HTTP_404_NOT_FOUND)

    def _perform_login(self, request, email, password):
        user = authenticate(email=email, password=password)
        if user is not None:
            token = get_token_for_user(user)
            return {
                'access': token['access'],
                'refresh': token['refresh'],
                'email': user.email,
                'username': user.username,
            }
        return None


class AccountCreateView(CreateAPIView):

    serializer_class = AccountSerializer