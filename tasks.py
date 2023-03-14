#!/usr/bin/env python3

from invoke import task, Collection
from pathlib import Path
from os import getuid, getgid, getcwd


@task
def clean(c):
    c.run("rm -f *.bin *.rpm")


@task
def build_binary(c):
    cmd = f'''
        {c.build.cri} run --rm -ti -v {getcwd()}:/repo -w /repo {c.build.container} /bin/bash -c "
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
            mv /dist/moneyctl /repo/{c.build.binary} && \
            chown {getuid()}:{getgid()} /repo/{c.build.binary}"
    '''
    if not Path(c.build.binary).is_file():
        c.run(cmd)


@task(pre=[build_binary])
def build_rpm(c):
    cmd = f'''
        {c.build.cri} run --rm -ti -v {getcwd()}:/repo -w /repo {c.build.container} /bin/bash -c "\
            dnf -y install rpmdevtools && \
            \
            rpmdev-setuptree && \
            cp /repo/{c.build.binary} /root/rpmbuild/BUILD/moneyctl && \
            cp /repo/moneyctl.rpm.spec /root/rpmbuild/SPECS/moneyctl.spec && \
            \
            rpmbuild -bb /root/rpmbuild/SPECS/moneyctl.spec && \
            \
            mv /root/rpmbuild/RPMS/x86_64/*.rpm /repo/ && \
            chown {getuid()}:{getgid()} /repo/*.rpm"
    '''
    if not list(Path('.').glob("*.rpm")):
        c.run(cmd)


ns = Collection(clean, build_binary, build_rpm)
ns.configure(
    {
        "run": {
            "echo": True,
        },
        "build": {
            "cri": "sudo podman",
            "container": "fedora:37",
            "binary": "binary.bin",
        }
    }
)
