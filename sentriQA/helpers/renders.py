from typing import Any, Protocol
from rest_framework import status
from rest_framework.response import Response



class ResponseInfo:

    @staticmethod
    def success_response(data: Any, message: str = "Success", status_code: int = status.HTTP_200_OK) -> Response:
        """
        Create a standardized success response.

        Args:
            data: Response payload
            message: Human-readable success message
            status_code: HTTP status code

        Returns:
            Response object with standardized structure
        """
        response = {
            "status": True,
            "data": data,
            "message": message,
            "status_code": status.HTTP_200_OK
        }
        return Response(response, status=status_code)
    
    @staticmethod
    def error_response(error: Any, message: str = "Error", status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
        """
        Create a standardized error response.

        Args:
            message: Human-readable error message
            error: Detailed error information (validation errors, etc.)
            status_code: HTTP status code

        Returns:
            Response object with standardized error structure
        """
        response = {
            "status": False,
            "data": error,
            "message": message,
            "status_code": status.HTTP_400_BAD_REQUEST
        }
        return Response(response, status=status_code)