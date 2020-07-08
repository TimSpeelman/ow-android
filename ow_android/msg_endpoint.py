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
                web.get('/inbox', self.handle_get_inbox),
                web.get('/peers', self.handle_get_peers),
                web.get('/send', self.handle_send_message),
                web.delete('/delete', self.handle_delete_message),
                ])    

    def initialize(self, session):
        super(MsgEndpoint, self).initialize(session)
        self.msg_overlay = session.get_overlay(MsgCommunity)

    def handle_send_message(self, request):
        msg = request.query['message']
        peer = request.query['mid']
        
        success = self.msg_overlay.send_message(peer, msg)
        
        return Response({ "success": success })

    def handle_get_inbox(self, request):
        return Response([{
            'id': m['id'],
            'sender_mid_b64': b64encode(m['peer'].mid).decode('utf-8'), 
            'message': m['message'].decode('utf-8'),
            'received_at': m['time'],
            } for m in self.msg_overlay.inbox])

    def handle_get_peers(self, request):
        peers = self.session.network.get_peers_for_service(self.msg_overlay.master_peer.mid)
        return Response([b64encode(p.mid).decode('utf-8') for p in peers])

    def handle_delete_message(self, request):
        message_id = request.query['id']
        success = self.msg_overlay.delete_message(message_id)
        return Response({ "success": success })

