# /usr/bin/env python3

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

    print("Computing the fingerprint of", os.path.basename(local))

    bsync.save_fingerprint(local)

    rawpatch_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rawpatch')

    print("Sending the rawpatch script to the remote system.")
    sh.scp(rawpatch_script, f"{login}:/tmp/")

    print(f"Sending the fingerprint to the remote system: {login}:/tmp/{fingerprint_name}")
    output = sh.scp(local_fingerprint, f"{login}:/tmp/")
    print_streams(output)

    print("Creating the rawpatch on the remote machine.")
    output = sh.ssh(login, f"/tmp/rawpatch --master {remote} --fingerprint {remote_fingerprint}")
    remote_patch = output.stdout.decode('utf8')
    print_streams(output)

    print("Downloading the patch from the remote machine.")
    output = sh.scp(f"{login}:{remote_patch}", f"{local_patch}")
    print_streams(output)

    print("Cleaning up the remote files")
    output = sh.ssh(login, f"rm {remote_fingerprint} {remote_patch}")
    print_streams(output)

    print("Applying the patch")
    #bsync.apply_rawpatch(local, local_patch)

    print("The patch has been applied! Deleting the patch file…")
    #sh.rm(local_patch)

    print("done")

if __name__ == '__main__':
    transfer()