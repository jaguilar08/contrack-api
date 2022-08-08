from typing import Literal

import requests

from const import APPLICATION_CODE, DGAPI_SERVER


class DGAPI(object):
    """DGAPI connection"""

    server_address = DGAPI_SERVER

    def __init__(self, headers: dict):
        self.headers = headers

    def send_request(self, type_method: Literal["POST", "GET"], endpoint: str, body: dict | None, headers: dict) -> requests.Response:
        if self.headers.get("content-length", False):
            self.headers.pop("content-length")
        new_headers = {"application-code": APPLICATION_CODE,
                       **self.headers, **headers}
        endpoint = f"http://{self.server_address}/{endpoint}"
        return requests.request(type_method, endpoint, json=body, headers=new_headers)

    def post(self, method: str, body: dict, headers: dict = {}) -> requests.Response:
        """
        Send POST request

        Parameters:
            method (str): Endpoint request
            body (dict): Body
            headers (dict): Headers
        """
        return self.send_request('POST', method, body, headers)

    def get(self, method: str, headers: dict = {}) -> requests.Response:
        """
        Send GET request

        Parameters:
            method (str): Endpoint request
            headers (dict): Headers
        """
        return self.send_request('GET', method, None, headers)
