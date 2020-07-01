from ipv8.REST.base_endpoint import BaseEndpoint, HTTP_BAD_REQUEST, HTTP_NOT_FOUND, Response
from aiohttp import web
from base64 import b64encode
import os

class GUIEndpoint(BaseEndpoint):
    """
    This endpoint is responsible for serving the GUI.
    """

    def __init__(self):
        super(GUIEndpoint, self).__init__()

    def setup_routes(self):
        path_to_root = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))
        path_to_static = os.path.join(path_to_root, 'static')
    
        self.app.add_routes([web.static('/', path_to_static, show_index=True)])

    def initialize(self, session):
        super(GUIEndpoint, self).initialize(session)
