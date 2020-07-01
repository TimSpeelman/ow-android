from ipv8.REST.base_endpoint import BaseEndpoint, HTTP_BAD_REQUEST, HTTP_NOT_FOUND, Response
from aiohttp import web
from base64 import b64encode
import json
import os

try:
    from android.storage import app_storage_path
    storage_path = app_storage_path()    
    print("Using android storage " + storage_path)
except:
    storage_path = os.path.join(os.getcwd(), 'temp')
    print("Using non-android storage " + storage_path)

class StateEndpoint(BaseEndpoint):
    """
    This endpoint is responsible for managing the front-end state.
    """

    path_to_state = ""

    def __init__(self):
        super(StateEndpoint, self).__init__()
        self.path_to_state = os.path.join(storage_path, 'state.json')

    def setup_routes(self):
        self.app.add_routes([web.get('', self.handle_get),
                             web.put('', self.handle_put)])    

    def initialize(self, session):
        super(StateEndpoint, self).initialize(session)

    def handle_get(self, request):
        if not os.path.exists(self.path_to_state):
            return Response(None)

        with open(self.path_to_state, 'r') as infile:
            data = json.load(infile)
            infile.close()

        return Response(data)

    async def handle_put(self, request):
        data = json.loads(await request.read())
        with open(self.path_to_state, 'w+') as outfile:
            json.dump(data, outfile)
            outfile.close()

        return Response({"success": True})
