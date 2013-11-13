import os, base64

SECRET_KEY_NON=os.urandom(24)
SECRET_KEY=base64.b64encode(SECRET_KEY_NON)
print SECRET_KEY

