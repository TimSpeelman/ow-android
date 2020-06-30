from ipv8.REST.base_endpoint import BaseEndpoint, HTTP_BAD_REQUEST, HTTP_NOT_FOUND, Response
from aiohttp import web
from base64 import b64encode

class HelloEndpoint(BaseEndpoint):
    """
    This endpoint is responsible for handing all requests regarding attestation.
    """

    def __init__(self):
        super(HelloEndpoint, self).__init__()

    def setup_routes(self):
        path_to_static = "ow_android/static"
        self.app.add_routes([web.static('/', path_to_static, show_index=True)])

    def initialize(self, session):
        super(HelloEndpoint, self).initialize(session)

    # async def handle_get(self, request):
    #     return Response({"hello": "world"})
