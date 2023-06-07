#!/usr/bin/env fish
exec podman run \
    --rm \
    -e _MONEYCTL_COMPLETE="$_MONEYCTL_COMPLETE" \
    -e COMP_CWORD="$COMP_CWORD" \
    -e COMP_WORDS="$COMP_WORDS" \
    --userns=keep-id \
    -u (id -u):(id -g) \
    -v $PWD:$PWD \
    -w $PWD \
    localhost/moneyctl:latest $argv
