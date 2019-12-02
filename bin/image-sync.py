#! /usr/bin/python3

import os

import click
import sh

import bsync


def print_streams(output):

    def print_stream(stream):
        if stream:
            print(stream.decode('utf8'))

    print_stream(output.stdout)
    print_stream(output.stderr)


@click.command()
@click.option('--local', '-l', required=True, type=click.Path(exists=True), help="The name of the local file.")
@click.option('--remote', '-r', required=True, type=click.STRING, help="The location of the file on the remote machine "
              "<username@host:/path/to/file>.")
def transfer(local, remote):
    login, remote_path = remote.split(':')

    local_fingerprint = local + '.fingerprint'

    fingerprint_name = os.path.basename(local_fingerprint)

    local_patch = local + '.rawpatch'

    remote_fingerprint = os.path.join('/tmp', fingerprint_name)

    fingerprint_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make-fingerprint')

    rawpatch_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rawpatch')

    print("Sending the rawpatch script to the remote system.")
    sh.scp(rawpatch_script, f"{login}:/tmp/")

    print("Sending the fingerprint script to the remote system.")
    sh.scp(fingerprint_script, f"{login}:/tmp/")

    print("Computing the master fingerprint on the remote machine…")
    remote_fingerprint_output = sh.ssh(login, f"/tmp/make-fingerprint --master {remote_path}", _bg=True)

    print("||  Meanwhile, computing the local fingerprint", os.path.basename(local))

    bsync.save_fingerprint(local)

    print(f"||  Sending the fingerprint to the remote system: {login}:/tmp/{fingerprint_name}")
    output = sh.scp(local_fingerprint, f"{login}:/tmp/")
    print_streams(output)

    print("||  waiting for the master fingerprint to be computed…")
    remote_fingerprint_output.wait()
    print_streams(remote_fingerprint_output)

    print("Creating the rawpatch on the remote machine.")
    output = sh.ssh(login, f"/tmp/rawpatch --master {remote_path} --fingerprint {remote_fingerprint}")
    remote_patch = output.stdout.decode('utf8')
    print_streams(output)

    if 'NoChanges' in remote_patch:
        print("The files are already identical.")
        print("Cleaning up the remote files")
        output = sh.ssh(login, f"rm {remote_fingerprint}")
        print_streams(output)
    else:
        print("Retrieving the patch from the remote machine.")
        output = sh.scp(f"{login}:{remote_patch}", f"{local_patch}")
        print("Cleaning up the remote files")
        output = sh.ssh(login, f"rm {remote_fingerprint} {remote_patch}")
        print_streams(output)

        print("Applying the patch")
        bsync.apply_rawpatch(local, local_patch)

        print("The patch has been applied! Deleting the patch file…")
        sh.rm(local_patch)

    print("Done!")

if __name__ == '__main__':
    transfer()

# time ./image-sync.py --local ~/VirtualBoxVMs/LODEEN\ 2.1\ beta\ 2/LODEEN_2.1_beta_2-disk002.vdi -r 'nrstickley@riemann:/home/nrstickley/LODEEN_2.1_beta_2-disk002.vdi'
# Sending the rawpatch script to the remote system.
# Sending the fingerprint script to the remote system.
# Computing the master fingerprint on the remote machine…
# ||  Meanwhile, computing the local fingerprint LODEEN_2.1_beta_2-disk002.vdi
# ||  Sending the fingerprint to the remote system: nrstickley@riemann:/tmp/LODEEN_2.1_beta_2-disk002.vdi.fingerprint
# ||  waiting for the master fingerprint to be computed…
# Finished making master fingerprint, /home/nrstickley/LODEEN_2.1_beta_2-disk002.vdi.fingerprint
# Creating the rawpatch on the remote machine.
# /home/nrstickley/LODEEN_2.1_beta_2-disk002.vdi.rawpatch
# Retrieving the patch from the remote machine.
# Cleaning up the remote files
# Applying the patch
# The patch has been applied! Deleting the patch file…
# Done!
# 
# real    0m38.679s
# user    1m28.157s
# sys     0m25.466s
