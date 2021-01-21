[[ $- != *i* ]] && return

which tmux >/dev/null 2>&1 || return

tmux_attach_via_proc() {
    # If the tmux package is upgraded during the lifetime of a
    # session, attaching with the new binary can fail due to different
    # protocol versions. This function attaches using the reference to
    # the old executable found in the /proc tree of an existing
    # session.
    pid=$(pgrep --newest tmux)
    if test -n "$pid"
    then
        /proc/$pid/exe attach
    fi
    return 1
}

if test -z "$TMUX"
then
    (tmux attach || tmux_attach_via_proc || tmux new-session)
fi
