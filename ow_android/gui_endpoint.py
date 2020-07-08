from ipv8.REST.base_endpoint import BaseEndpoint, HTTP_BAD_REQUEST, HTTP_NOT_FOUND, Response
from aiohttp import web
from base64 import b64encode
import os

class GUIEndpoint(BaseEndpoint):
    """
    This endpoint is responsible for serving the GUI.
    """

    files_dir = ""

    def __init__(self, files_dir):
        super(GUIEndpoint, self).__init__()
        self.files_dir = files_dir

    def setup_routes(self):
        # path_to_root = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))
        # path_to_static = os.path.join(path_to_root, 'static')
    
        self.app.add_routes([web.static('/', files_dir, show_index=True)])

    def initialize(self, session):
        super(GUIEndpoint, self).initialize(session)
