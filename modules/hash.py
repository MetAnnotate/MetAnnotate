import hashlib


# give the name of file, return md5 digest
def md5hash(file, buf_size=65536):
    # buf_size is totally arbitrary, change for your app!
    md5 = hashlib.md5()

    with open(file, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


# given a hashable object, hash to hexadecimal string
def hexhash(obj):
    s = str(hex(hash(obj)))
    return s.split('x')[1]
