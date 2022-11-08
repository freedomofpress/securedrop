#!/bin/bash
## Show (and opportunistically copy) the current development OTP (to the
## clipboard)

if [ -n "$(command -v oathtool)" ]; then
    OTP=$(oathtool --totp --base32 JHCOGO7VCER3EJ4L)
    echo "$OTP"

    COPY=$(command -v wl-copy)
    [ -z "$COPY" ] && COPY="$(command -v xclip)"
    [ $? -eq 0 ] && [ -n "$COPY" ] && COPY="$COPY -selection clipboard"
    [ -z "$COPY" ] && COPY=$(command -v pbcopy)
    
    [ -n "$COPY" ] && echo "$OTP" | $COPY
    [ $? -eq 0 ] && echo "The one time password was copied to your clipboard"
    exit 0
else
    echo "Please install \`oathtool\` to use this script!"
fi
