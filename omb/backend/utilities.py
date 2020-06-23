import msgpack


def read_msgpack(path):
    with open(path, 'rb') as f:
        data = msgpack.unpackb(f.read())
    return data


def write_msgpack(path, data):
    with open(path, 'wb') as f:
        f.write(msgpack.packb(data))
