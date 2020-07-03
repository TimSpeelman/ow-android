from binascii import unhexlify
from ipv8.community import Community
from ipv8.keyvault.crypto import ECCrypto
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.lazy_payload import VariablePayload, vp_compile
from ipv8.peer import Peer
from ipv8_service import IPv8

@vp_compile
class MyMessage(VariablePayload):
   format_list = ['varlenI'] # When reading data, we unpack an unsigned integer from it.
   names = ["message"] 

class MsgCommunity(Community):

   master_peer = Peer(unhexlify("307e301006072a8648ce3d020106052b81040024036a000400bd9cae587628a7d169fa193729465b4d"
                                "2e4a382b5fac38e356a225339e8ff5336c70fd426d173796090416be826bcc5730533a0000e5c6db19"
                                "107f6930d3c3a1017fe131fa396840e4facd620add83dadbd4d79185d4eabdf843efc292d7f898af46"
                                "297c76736c"))

   def __init__(self, my_peer, endpoint, network):
       super(MsgCommunity, self).__init__(my_peer, endpoint, network)
       # Register the message handler for messages with the identifier "1".
       self.add_message_handler(1, self.on_message)

   def started(self):
       async def start_communication():
            for p in self.get_peers():
                self.send_message(p.address)
       self.register_task("start_communication", start_communication, interval=5.0, delay=0)

   def send_message(self, address):
       # Send a message with our digital signature on it.
       # We use the latest version of our Lamport clock.
       print("Sending message")
       self.endpoint.send(address, self.ezr_pack(1, MyMessage("Hello World".encode('utf-8'))))

   @lazy_wrapper(MyMessage)
   def on_message(self, peer, payload):
       print(self.my_peer, "says", payload.message)
