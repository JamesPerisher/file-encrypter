import os
import sys
import time
import struct
import random
import getpass
import hashlib
from Crypto.Cipher import AES


INTERMEDIATE_KEY_FILENAME = "IntermediateKey.dat"
FILES_DIR = "data"


class Drive:
    def __init__(self, drive=None):
        if not os.path.exists(drive):
            raise FileNotFoundError("No such file or directory: '%s'"%drive)
            return

        self.drive = drive

        if not (INTERMEDIATE_KEY_FILENAME in os.listdir(self.drive)):
            File.make_file(self.drive, INTERMEDIATE_KEY_FILENAME)

        if not (FILES_DIR in os.listdir(self.drive)):
            try:
                os.mkdir(os.path.join(self.drive, FILES_DIR))
            except FileExistsError():
                pass


        self.keyfile = File(os.path.join(self.drive, INTERMEDIATE_KEY_FILENAME))

    def get_drive(self):
        return self.drive

    def get_files(self):
        return os.listdir(self.drive)

    def get_file(self, file):
        return os.path.join(self.drive, file)


class VertualFile(str):
    def __init__(self, method="t"):
        self.method = list(method)
        self.data = b'' if "b" in self.method else ""

    def truncate(self):
        self.data = b'' if "b" in self.method else ""

    def read(self):
        return self.data

    def write(self, data):
        self.data = self.data + data

class File(VertualFile):
    def __init__(self, file, chunksize=64*1024):
        super().__init__("b")
        self.testfile(file)
        self.chunksize = chunksize

        self.file = file

    def __repr__(self):
        return self.file

    def read_raw(self, key):
        filesize = os.path.getsize(self)
        with open(self, "rb") as f:

            data = f.read()

            x = struct.calcsize('Q')
            origsize = struct.unpack('<Q', data[0:x])[0]
            iv = data[x:x+16]
            data = data[16+x::]

            key.update_iv(iv)


            return key.decrypt(File.pad(data))

    def write_raw(self, key, data):
        filesize = os.path.getsize(self)
        with open(self, "wb") as f:
            f.truncate()
            f.write(struct.pack('<Q', filesize))
            f.write(key.iv)

            f.write(key.encrypt(File.pad(data)))


    def encrypt_file(self, key, out_filename=None):
        File.testfile(self)

        iv = key.new_iv()
        filesize = os.path.getsize(self.file)

        with open(self.file, 'rb') as infile:
            with open(out_filename, 'wb') as outfile:
                outfile.write(struct.pack('<Q', filesize))
                outfile.write(iv)

                while True:
                    chunk = infile.read(self.chunksize)
                    if len(chunk) == 0:
                        break
                    elif len(chunk) % 16 != 0:
                        chunk += b' ' * (16 - len(chunk) % 16)

                    outfile.write(key.encrypt(chunk))

    def decrypt_file(self, key, out_filename=None):
        File.testfile(self)

        with open(self, 'rb') as infile:
            origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
            iv = infile.read(16)
            key.update_iv(iv)

            with open(out_filename, 'wb') as outfile:
                while True:
                    chunk = infile.read(self.chunksize)
                    if len(chunk) == 0:
                        break
                    xxxx = File.pad(chunk)
                    outfile.write(key.decrypt(xxxx))

                outfile.truncate(origsize)

    @staticmethod
    def pad(data):
        if len(data) == 0:
            return data
        elif len(data) % 16 != 0:
            data += b' ' * (16 - len(data) % 16)

        return data

    @staticmethod
    def make_file(path, name):
        full = os.path.join(path, name)
        if os.path.exists(full):
            raise FileExistsError("File '%s' already exists."%full)
            return

        if not os.path.exists(path) and path != '':
            raise FileNotFoundError("No such file or directory: '%s'"%path)
            return

        open(full, "w").close()

    @staticmethod
    def testfile(file):
        try:
            File.make_file(*os.path.split(file))
            return True
        except FileExistsError:
            return True

        return False



class Key:
    def _make_key(self, current, iv=None):
        if current == self.last:
            return
        if self.last == "NEW":
            return

        self.iv = self.iv if iv == None else iv
        self.last == current
        self.key = AES.new(self.key_raw, AES.MODE_CBC, self.iv)

    def update_iv(self, iv):
        self.last == "NEW"
        self.iv = iv
        self.key = AES.new(self.key_raw, AES.MODE_CBC, self.iv)

    def new_iv(self):
        iv = struct.pack("16B", *[random.randint(0, 0xFF) for i in range(16)])
        self.update_iv(iv)
        return iv

    def __init__(self, key, iv = None, user_key=None):
        self.last = ""
        self.key_raw = key
        self.new_iv()
        self._make_key("NEW")
        self.user_key = user_key

    def __repr__(self):
        return "Key: %s"%str(self.key)

    def encrypt(self, data):
        self._make_key("EN")
        return self.key.encrypt(data)

    def decrypt(self, data):
        if len(data) == 0:
            return b''

        self._make_key("DE")
        return self.key.decrypt(data)

    @staticmethod
    def from_hex(hex_val, iv=None):
        try:
            return Key(bytes.fromhex(hex_val), iv)
        except:
            return False


class KeyFile:
    def __init__(self, drive):
        self.f = File(drive.keyfile)

    def _get_key(self, key):
        try:
            x = self.f.read_raw(key)
            return x.decode()
        except UnicodeDecodeError:
            pass
        except Exception as e:
            self.set_key(key)
            return self.f.read_raw(key).decode()


    def get_key(self, key):
        key = self._get_key(key).split("\n")[1]
        return key


    def set_key(self, key):
        new_key = struct.pack("32B", *[random.randint(0, 0xFF) for i in range(32)])

        self._set_key(key, new_key)


    def _set_key(self, key, new_key):
        self.f.write_raw(key, ("-----BEGIN MASTER ENCRYPTION KEY-----\n%s\n-----END MASTER ENCRYPTION KEY-----"%(new_key.hex())).encode())
        return True



def _verify(f, user_key):
    user_key = Key(hashlib.sha256(user_key.encode()).digest())
    try:
        xx = f.get_key(user_key)
    except AttributeError:
        print("Incorrect please wait.")
        time.sleep(3)
        return
    master_key = Key.from_hex(xx)
    master_key.user_key = user_key
    if master_key:
        return master_key

def verify(f):
    while True:
        master_key = _verify(f, getpass.getpass())
        if master_key:
            break
    return master_key

def main(config):
    drive = Drive(config.get("drive", "D:\\"))
    f = KeyFile(drive)

    master_key = verify(f)

    return drive, master_key, config



if __name__ == '__main__':
    drive, master_key = main("D:\\")
