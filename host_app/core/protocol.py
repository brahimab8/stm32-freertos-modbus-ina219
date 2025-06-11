import json
from .paths import PROTO_FILE

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
