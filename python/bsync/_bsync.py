"""
Tools for synchronizing large, fixed-size files (disk images) so that only the sections that contain changes need to
be transferred over a network. The perfromance is better than that of rsync, due to multiprocessing and the restricted
use-case (fixed-size) files.
"""
import os
import hashlib
import math
import multiprocessing as mp

import msgpack
import zstd


CHUNK_SIZE = 4 * 1024 * 1024


def hash_it(data):
    r = hashlib.sha1(data)
    return r.digest()


def gen_hashes(filename):
    f = open(filename, 'rb')
    data = f.read(CHUNK_SIZE)
    i = 0
    while len(data) > 0:
        yield i, hash_it(data)
        i += 1
        data = f.read(CHUNK_SIZE)
    f.close()


def pool_init(*fname):
    name = "".join(fname)
    process = mp.current_process()
    process.fd = open(name, 'rb')


def hash_of_chunk(chunk_index):
    process = mp.current_process()
    process.fd.seek(chunk_index * CHUNK_SIZE)
    data = process.fd.read(CHUNK_SIZE)
    return chunk_index, hash_it(data)


def make_fingerprint(filename: str) -> dict:
    """Compute hashes for chunks of the specified file and output a dictionary of the hashes"""
    file_size = os.path.getsize(filename)

    n_chunks = math.ceil(file_size / CHUNK_SIZE)

    if n_chunks < 13:  # don't bother using multiprocessing for such small files
        hashes = gen_hashes(filename)
    else:
        n_threads = mp.cpu_count()
        n_tasks = 1 if n_threads == 1 else n_threads // 2
        pool = mp.Pool(n_tasks, initializer=pool_init, initargs=filename)
        hashes = pool.map(hash_of_chunk, range(n_chunks))

    return {i : h for i, h in hashes}


def compare_fingerprints(old: dict, new: dict) -> list:
    """Identify which chunks differ between the old and new lists of hashes."""
    if len(old) != len(new):
        raise AssertionError("the old and new fingerprints must be of the same size")

    differing_indices = []

    for i, old_hash in old.items():
        if old_hash != new[i]:
            differing_indices.append(i)
    return differing_indices


def save_msg(filename: str, data):
    """Save object data to a file"""
    with open(filename, 'wb') as f:
        msgpack.dump(data, f)


def load_msg(filename: str) -> list:
    """Load a list of hashes"""
    with open(filename, 'rb') as f:
        hashes = msgpack.load(f)
    return hashes


def what_changed(filename: str, fingerprint: str) -> list:
    """Determine which chunks changed between the current version and the hashed version"""
    old_fingerprint = load_msg(fingerprint)

    current_fingerprint = make_fingerprint(filename)

    return compare_fingerprints(old_fingerprint, current_fingerprint)


def save_fingerprint(datafile: str):
    """Compute and save the datafile's fingerprint"""
    fingerprint = make_fingerprint(datafile)

    fingerprint_filename = datafile + ".fingerprint"

    save_msg(fingerprint_filename, fingerprint)


def compute_rawpatch(new_file: str, diff_indices):
    f = open(new_file, 'rb', CHUNK_SIZE)

    patch = {}

    for i in diff_indices:
        f.seek(i * CHUNK_SIZE)
        patch[i] = f.read(CHUNK_SIZE)

    return patch


def save_rawpatch(filename: str, rawpatch: dict):
    compressed_patch = zstd.compress(msgpack.dumps(rawpatch), 5)

    with open(filename, 'wb') as f:
        f.write(compressed_patch)


def make_rawpatch(filename: str, fingerprint: str):
    changes = what_changed(filename, fingerprint)

    if len(changes) == 0:
        print("The file has not changed since the last fingerprint was created.")
        return

    rawpatch = compute_rawpatch(filename, changes)

    save_rawpatch(filename + '.rawpatch', rawpatch)


def apply_rawpatch(old_file: str, rawpatch: str):
    with open(rawpatch, 'rb') as f:
        compressed_patch = f.read()

    # FIXME: patch may not fit into memory, even if compressed patch does.

    patch = msgpack.loads(zstd.uncompress(compressed_patch))

    f = open(old_file, 'r+b')

    for i, chunk in patch.items():
        f.seek(i * CHUNK_SIZE)
        f.write(chunk)

    f.close()


# general steps when performing a typical update on a 60 GB disk image:

# 1. The client computes the fingerprint of their version of the file, using save_fingerprint()  ~ 30 seconds
# 2. The client sends the fingerprint to the server.                                             ~ 0 seconds
# 3. The server compares the master version of the disk image to the client's fingerprint and
#    creates a raw patch, using make_rawpatch()                                                  ~ 30 seconds
# 4. The server sends the raw patch back to the client.                                          ~ 2 - 10 seconds
# 5. The client applies the raw patch to their version of the file, using apply_rawpatch() and
#    now has a copy that is identical to the master.                                             ~ 1 - 4 seconds

# total time: 1 minute 7 seconds

# total time needed to copy the entire file over the network: ~ 9 minutes

