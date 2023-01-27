#!/usr/bin/env bash

set -euxo pipefail


CONTAINER_CMD="sudo podman"


function build-bin {
    container="fedora:37"

    $CONTAINER_CMD run --rm -ti -v $(pwd):/repo -w /repo $container /bin/bash -c "
        dnf -y install make automake gcc gcc-c++ kernel-devel python3-devel python3-pip poetry && \
        pip3 install pyinstaller && \
        \
        poetry export | pip3 install -r /dev/stdin && \
        \
        pyinstaller --noconfirm --onefile \
            --collect-data beancount \
            --collect-submodules beancount \
            --name moneyctl \
            --workpath /build \
            --distpath /dist \
            --specpath /spec \
            moneyctl/__init__.py && \
        \
        mv /dist/moneyctl /repo/moneyctl.bin && \
        chown $(id -u):$(id -g) /repo/moneyctl.bin"
}

function build-rpm {
    container="fedora:37"

    $CONTAINER_CMD run --rm -ti -v $(pwd):/repo -w /repo $container /bin/bash -c "\
        dnf -y install rpmdevtools && \
        \
        rpmdev-setuptree && \
        cp /repo/moneyctl.bin /root/rpmbuild/BUILD/moneyctl && \
        cp /repo/moneyctl.rpm.spec /root/rpmbuild/SPECS/moneyctl.spec && \
        \
        rpmbuild -bb /root/rpmbuild/SPECS/moneyctl.spec && \
        \
        mv /root/rpmbuild/RPMS/x86_64/*.rpm /repo/ && \
        chown $(id -u):$(id -g) /repo/*.rpm"
}


function main {
    case $1 in
        bin)
            build-bin
            ;;
        rpm)
            [[ -f "moneyctl.bin" ]] || build-bin
            build-rpm
            ;;
        clean)
            rm -f *.bin *.rpm
            ;;
        help)
            echo "./build.sh (bin|rpm|clean)"
            ;;
    esac
}

main $*