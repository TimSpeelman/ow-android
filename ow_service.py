import json
import os
import shutil
import signal
import sys
import argparse

from asyncio import all_tasks, ensure_future, gather, get_event_loop, sleep
from base64 import b64encode

from ipv8_service import IPv8
from ipv8.configuration import get_default_configuration
from ipv8.REST.rest_manager import RESTManager
from ow_android.gui_endpoint import GUIEndpoint
from ow_android.state_endpoint import StateEndpoint
from ow_android.msg_overlay import MsgCommunity
from ow_android.msg_endpoint import MsgEndpoint
from ow_android.attributes_endpoint import AttributesEndpoint
from ipv8.keyvault.crypto import ECCrypto


try:
    from android.storage import app_storage_path    
    # On android, default to the app storage
    default_storage_path = app_storage_path()    
    print("Default android storage " + default_storage_path)  
except:
    # On non-android, default to current working directory
    default_storage_path = os.getcwd()
    print("Default non-android storage " + default_storage_path)

# Launch OpenWalletService.

class OpenWalletService(object):

    def __init__(self):
        self._stopping = False

    async def start(self, args):

        port = args.port
        # if `args.workdir` is absolute, it will ignore `default_storage_path`
        workdir = os.path.join(default_storage_path, args.workdir) 
        fresh = args.fresh
        loglevel = args.loglevel

        # Give the peer its own working directory
        if os.path.exists(workdir):
            if fresh:
                shutil.rmtree(workdir)
                os.mkdir(workdir)
        else:
            os.mkdir(workdir)

        # Set up its IPv8 Configuration
        configuration = get_default_configuration()
        configuration['logger']['level'] = loglevel
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

        # Add my custom overlays
        msg_overlay_config = {
            'class': 'MsgCommunity',
            'key': "anonymous id",
            'walkers': [
                {
                    'strategy': "RandomWalk",
                    'peers': 20,
                    'init': {
                        'timeout': 3.0
                    }
                },
            ],
            'initialize': {},
            'on_start': [('started', )]
        }
        configuration['overlays'].append(msg_overlay_config)

        # Provide the working directory to its overlays
        working_directory_overlays = ['AttestationCommunity', 'IdentityCommunity', 'TrustChainCommunity']
        for overlay in configuration['overlays']:
            if overlay['class'] in working_directory_overlays:
                overlay['initialize'] = {'working_directory': workdir}

        # Start its IPv8 service
        ipv8 = IPv8(configuration, extra_communities={'MsgCommunity': MsgCommunity})
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

        if os.getenv is None:
            print("OWSERVICE ANDROID PRIVATE IS NONE")

        priv = os.getenv("ANDROID_PRIVATE", os.getcwd())

        print("OWSERVICE Files in " + priv) 
        for root, dirs, files in os.walk(priv):
            for filename in files:
                print(filename)

        a1 = os.path.join(priv, "src")
        a2 = os.path.join(a1, "main")
        a3 = os.path.join(a2, "assets")

        print("OWSERVICE Files in " + a1)
        for root, dirs, files in os.walk(a1):
            for filename in files:
                print(filename)

        print("OWSERVICE Files in " + a2)
        for root, dirs, files in os.walk(a2):
            for filename in files:
                print(filename)

        print("OWSERVICE Files in " + a3)
        for root, dirs, files in os.walk(a3):
            for filename in files:
                print(filename)

        guidir = os.path.join(priv, "src", "main", "assets", "gui")

        # Start its API
        api = RESTManager(ipv8)
        endpoints = {
                '/app': GUIEndpoint(guidir),
                '/state': StateEndpoint(workdir),
                '/msg': MsgEndpoint(),
                '/attributes': AttributesEndpoint(workdir),
            }

        await api.start(port=port, endpoints=endpoints)

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
    parser.add_argument('--port', '-p', action='store', type=int, default=8642, help='Port number')
    parser.add_argument('--workdir', '-w', action='store', default='temp', help='The working directory')
    parser.add_argument('--fresh', '-f', action='store_true', help='Refresh the identity')
    parser.add_argument('--loglevel', '-l', action='store', default='ERROR', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='The log level')

    args = parser.parse_args(sys.argv[1:])

    service = OpenWalletService()
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