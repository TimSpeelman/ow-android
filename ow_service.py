import json
import os
import shutil
import signal
import sys
import argparse

from asyncio import all_tasks, ensure_future, gather, get_event_loop, sleep
from base64 import b64encode

from ipv8_service import IPv8 # FIXME
from ipv8.configuration import get_default_configuration
from ipv8.REST.rest_manager import RESTManager
from ow_android.hello_endpoint import HelloEndpoint

# Launch OpenWalletService.
# - Defaults to port 13310

class OpenWalletService(object):

    default_port = 13310
    workdir = "temp"

    def __init__(self):
        self._stopping = False

    async def start(self, args):

        port = self.default_port
        workdir = self.workdir
        fresh = False

        # Give the peer its own working directory
        if os.path.exists(workdir):
            if fresh:
                shutil.rmtree(workdir)
                os.mkdir(workdir)
        else:
            os.mkdir(workdir)

        # Set up its IPv8 Configuration
        configuration = get_default_configuration()
        configuration['logger']['level'] = "ERROR"
        configuration['keys'] = [
            {
                'alias': "anonymous id", 
                'generation': u"curve25519",
                'file': u"%s/multichain.pem" % (workdir)
            },
            {
                'alias': "my peer",
                'generation': u"medium",
                'file': u"%s/ec.pem" % (workdir)
            }
        ]
        
        # Only load the basic communities
        requested_overlays = [
            'AttestationCommunity', 
            'IdentityCommunity', 
            'DHTDiscoveryCommunity',
            'DiscoveryCommunity'
        ]
        configuration['overlays'] = [o for o in configuration['overlays'] if o['class'] in requested_overlays]

        # Provide the working directory to its overlays
        working_directory_overlays = ['AttestationCommunity', 'IdentityCommunity', 'TrustChainCommunity']
        for overlay in configuration['overlays']:
            if overlay['class'] in working_directory_overlays:
                overlay['initialize'] = {'working_directory': workdir}

        # Start its IPv8 service
        ipv8 = IPv8(configuration)
        await ipv8.start()

        # Print the peer for reference
        url = "http://localhost:%d" % port
        mid_b64 = b64encode(ipv8.keys["anonymous id"].mid).decode('utf-8')

        print("Starting OpenWalletService at %s" % url)
        print("OpenWalletService me: %s/me" % url)
        print("OpenWalletService app: %s/app" % url)
        print("OpenWalletService workdir: %s" % workdir)
        print("OpenWalletService mid_b64: %s" % mid_b64)

        data = {
            'port': port,
            'mid_b64': mid_b64,
        }

        with open('%s/config.json' % workdir, 'w') as outfile:
            json.dump(data, outfile)
            outfile.close()

        # Start its API
        api = RESTManager(ipv8)
        await api.start(port, {'/app':HelloEndpoint})

         # Handle shut down
        async def signal_handler(sig):
            print("Received shut down signal %s" % sig)
            if not self._stopping:
                self._stopping = True

                print("Stopping peer..")
                if api:
                    await api.stop()
                await ipv8.stop()
                
                await gather(*all_tasks())
                get_event_loop().stop()

        signal.signal(signal.SIGINT, lambda sig, _: ensure_future(signal_handler(sig)))
        signal.signal(signal.SIGTERM, lambda sig, _: ensure_future(signal_handler(sig)))


def main(argv):
    parser = argparse.ArgumentParser(add_help=False, description=('Starts OpenWallet as a service'))
    parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
    # parser.add_argument('--no-rest-api', '-a', action='store_const', default=False, const=True, help='Autonomous: disable the REST api')
    # parser.add_argument('--statistics', '-s', action='store_const', default=False, const=True, help='Enable IPv8 overlay statistics')

    service = OpenWalletService()

    args = parser.parse_args(sys.argv[1:])
    loop = get_event_loop()
    coro = service.start(args)
    ensure_future(coro)

    if sys.platform == 'win32':
        # Unfortunately, this is needed on Windows for Ctrl+C to work consistently.
        # Should no longer be needed in Python 3.8.
        async def wakeup():
            while True:
                await sleep(1)
        ensure_future(wakeup())

    loop.run_forever()

if __name__ == "__main__":
    main(sys.argv[1:])