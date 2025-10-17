from typing import Any, Protocol
from rest_framework import status
from rest_framework.response import Response



class ResponseInfo:

    def __init__(self, user=None, **args) -> None:
        self.response = {
            "status": args.get('status', True),
            "status_code": args.get('status_code', ''),
            "data": args.get('data', {}),
            "message": args.get('message', '')
        }

    @staticmethod
    def _success_response(data: Any, message: str = "Success", status_code: int = status.HTTP_200_OK) -> Response:
        response = {
            "status": True,
            "data": data,
            "message": message,
            "status_code": status.HTTP_200_OK
        }
        return Response(response, status=status_code)
    
    @staticmethod
    def _error_response(error: Any, message: str = "Error", status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
        response = {
            "status": False,
            "data": error,
            "message": message,
            "status_code": status.HTTP_400_BAD_REQUEST
        }
        return Response(response, status=status_code)