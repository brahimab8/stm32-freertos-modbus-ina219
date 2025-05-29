import json
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir, os.pardir))
META_DIR = os.path.join(REPO_ROOT, 'metadata')
PROTO_FILE = os.path.join(META_DIR, 'protocol.json')

class Protocol:
    def __init__(self, path=PROTO_FILE):
        with open(path, 'r') as f:
            data = json.load(f)
        self.constants    = data['constants']
        self.commands     = data['commands']
        self.status_codes = data['status_codes']
        self.sensors      = data['sensors']

# singleton instance
protocol = Protocol()
protocol.sensors = {k.lower(): v for k, v in protocol.sensors.items()}
