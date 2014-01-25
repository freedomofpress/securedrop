import os, base64

SECRET_KEY_NON=os.urandom(32)
SECRET_KEY=base64.b64encode(SECRET_KEY_NON)

print SECRET_KEY

