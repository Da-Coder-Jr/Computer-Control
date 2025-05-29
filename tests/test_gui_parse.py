from computer_control.core import manager
import json

def test_parse_drag():
    raw='{"thought":"drag","operation":"drag","x1":1,"y1":1,"x2":10,"y2":10}'
    op=json.loads(raw)
    assert op["operation"]=="drag"
