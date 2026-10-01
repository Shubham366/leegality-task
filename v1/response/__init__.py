from fastapi.responses import JSONResponse
from http import HTTPStatus


class BadRequest(Exception):
    def __init__(self, message: str = "bad request"):
        self.message = message
        super().__init__(message)


class NotFound(Exception):
    def __init__(self, message: str = "not found"):
        self.message = message
        super().__init__(message)


class ApiResponse:
    @staticmethod
    def response_ok(data=None, message="success"):
        response = {
            "status": HTTPStatus.OK,
            "message": message,
            "data": data,
        }
        return JSONResponse(content=response,status_code=HTTPStatus.OK)

    @staticmethod
    def response_error(message="error", data=None):
        response = {
            "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            "message": message,
            "data": data,
        }
        return JSONResponse(content=response,status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

    @staticmethod
    def response_bad_request(message="bad request", data=None):
        response = {
            "status": HTTPStatus.BAD_REQUEST,
            "message": message,
            "data": data,
        }
        return JSONResponse(content=response, status_code=HTTPStatus.BAD_REQUEST)

    @staticmethod
    def response_not_found(message="not found", data=None):
        response = {
            "status": HTTPStatus.NOT_FOUND,
            "message": message,
            "data": data,
        }
        return JSONResponse(content=response, status_code=HTTPStatus.NOT_FOUND)
    
    @staticmethod
    def response_created(
        message="Resource created",
        code=201,
        success=True,
        data={},
        paginator={},
        exp=(None, None, None),
    ):
        # message = message_format(message)
        data = {
            "message": message,
            "status": HTTPStatus.CREATED,
            "success": success,
            "data": data,
            "paginator": paginator,
        }
        return JSONResponse(content=data, status_code=code)