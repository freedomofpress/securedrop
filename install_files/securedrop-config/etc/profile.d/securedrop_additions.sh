[[ $- != *i* ]] && return

which tmux >/dev/null 2>&1 || return

function tmux_attach_via_proc() {
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
