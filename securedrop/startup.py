import sys
from typing import Optional

from encryption import EncryptionManager
from flask import Flask

import redwood


def validate_journalist_key(app: Optional[Flask] = None) -> bool:
    """Verify the journalist PGP key is valid"""
    encryption_mgr = EncryptionManager.get_default()
    # First check that we can read it
    try:
        journalist_key = encryption_mgr.get_journalist_public_key()
    except Exception as e:
        if app:
            print(f"ERROR: Unable to read journalist public key: {e}", file=sys.stderr)
            app.logger.error(f"ERROR: Unable to read journalist public key: {e}")
        return False
    # And then what we read is valid
    try:
        redwood.is_valid_public_key(journalist_key)
    except redwood.RedwoodError as e:
        if app:
            print(f"ERROR: Journalist public key is not valid: {e}", file=sys.stderr)
            app.logger.error(f"ERROR: Journalist public key is not valid: {e}")
        return False

    return True
