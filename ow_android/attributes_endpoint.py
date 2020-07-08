from ipv8.REST.base_endpoint import BaseEndpoint, HTTP_BAD_REQUEST, HTTP_NOT_FOUND, Response
from aiohttp import web
from base64 import b64encode
import json
import os


class AttributesEndpoint(BaseEndpoint):
    """
    This endpoint is responsible for managing attributes.
    """

    path_to_state = ""

    def __init__(self, storage_dir):
        super(AttributesEndpoint, self).__init__()
        self.path_to_state = os.path.join(storage_dir, 'attributes.json')

    def setup_routes(self):
        self.app.add_routes([web.get('', self.handle_get),
                             web.post('', self.handle_post)])    

    def initialize(self, session):
        super(AttributesEndpoint, self).initialize(session)

    def handle_get(self, request):
        return Response(self._get_attributes())

    async def handle_post(self, request):
        data = self._get_attributes()
        attribute =  json.loads(await request.read())
        
        # TODO Validate

        data.append(attribute)

        with open(self.path_to_state, 'w+') as outfile:
            json.dump(data, outfile)
            outfile.close()

        return Response({"success": True})

    def _get_attributes(self): 
        if not os.path.exists(self.path_to_state):
            return []

        with open(self.path_to_state, 'r') as infile:
            data = json.load(infile)
            infile.close()

        return data
