import base64

def uuencode(s):
    return base64.b64encode(s.encode()).decode()

def uudecode(s):
    return base64.b64decode(s.encode()).decode()
