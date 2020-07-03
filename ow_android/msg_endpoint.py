from ipv8.REST.base_endpoint import BaseEndpoint, HTTP_BAD_REQUEST, HTTP_NOT_FOUND, Response
from aiohttp import web
from base64 import b64encode
import json
import os
from .msg_overlay import MsgCommunity


class MsgEndpoint(BaseEndpoint):
    """
    This endpoint is responsible for sending custom messages to peers.
    """

    msg_overlay = None

    def __init__(self):
        super(MsgEndpoint, self).__init__()

    def setup_routes(self):
        self.app.add_routes([
                web.get('/peers', self.handle_get_peers),
                web.get('/send', self.handle_send_message)
                ])    

    def initialize(self, session):
        super(MsgEndpoint, self).initialize(session)
        self.msg_overlay = session.get_overlay(MsgCommunity)

    def handle_send_message(self, request):
        msg = request.query['message']
        peer = request.query['mid']
        
        self.msg_overlay.send_message(peer, msg)
        
        return Response({ "success": True })

    def handle_get_peers(self, request):
        peers = self.session.network.get_peers_for_service(self.msg_overlay.master_peer.mid)
        return Response([b64encode(p.mid).decode('utf-8') for p in peers])

