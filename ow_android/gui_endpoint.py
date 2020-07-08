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
        self.files_dir = files_dir
        super(GUIEndpoint, self).__init__()

    def setup_routes(self):
        print("Static GUI files served from " + self.files_dir)
        self.app.add_routes([web.static('/', self.files_dir, show_index=True)])

    def initialize(self, session):
        super(GUIEndpoint, self).initialize(session)
