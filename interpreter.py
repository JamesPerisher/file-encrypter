import os
import time
import hashlib
import getpass
import colorama
import encrypter
from colorama import Fore, Back, Style

from config import config

LOG =      Style.NORMAL + Back.BLACK + Fore.WHITE
INFO =     Style.NORMAL + Back.BLACK + Fore.CYAN
WARN =     Style.NORMAL + Back.BLACK + Fore.YELLOW
ERROR =    Style.NORMAL + Back.BLACK + Fore.RED
PASSWORD = Style.NORMAL + Back.BLUE + Fore.BLUE
SUCCESS =  Style.NORMAL + Back.BLACK + Fore.GREEN


colorama.init()


def iigetpass(txt=""):
    console.custom(txt, end="")
    return getpass.getpass()

def prompt(txt=""):
    console.custom()

    return Input(LOG + "%s%s $~ "%(os.getlogin(), txt))


class Input():
    def __init__(self, txt=""):
        self.raw = console.log.input(txt) + " "*100
        self.argsraw = ((self.raw.strip().split(maxsplit=1))+["",""]) [1]
        self.i = [x.strip() for x in self.raw.strip().split()]

    def iscmd(self, *args, n=0):
        try:
            return self.i[n] in [x.strip() for x in args]
        except IndexError:
            return False

    def get(self, n=0):
        try:
            return self.i[n]
        except IndexError:
            return None


class console:
    def input(*args, end=""):
        console.custom(console.join(" ", args), end=end)
        return input()


    def join(split, items):
        return str(split).join([str(x) for x in items])

    def custom(*args, end="\n"):
        print(console.join("", args), end=end)

    def log(*args, end="\n"):
        console.custom(LOG,      console.join(" ", args), end=end)

    def info(*args, end="\n"):
        console.custom(INFO,     console.join(" ", args), end=end)

    def warn(*args, end="\n"):
        console.custom(WARN,     console.join(" ", args), end=end)

    def error(*args, end="\n"):
        console.custom(ERROR,    console.join(" ", args), end=end)

    def password(*args, end="\n"):
        console.custom(PASSWORD, console.join(" ", args), end=end)

    def success(*args, end="\n"):
        console.custom(SUCCESS,  console.join(" ", args), end=end)

console.log.input      = lambda *args : console.input(LOG,      *args)
console.info.input     = lambda *args : console.input(INFO,     *args)
console.warn.input     = lambda *args : console.input(WARN,     *args)
console.error.input    = lambda *args : console.input(ERROR,    *args)
console.password.input = lambda *args : console.input(PASSWORD, *args)
console.success.input  = lambda *args : console.input(SUCCESS,  *args)


class res:
    def __init__(self, interpreter):
        self.int = interpreter

    def response(function):
        def new_function(*args, **kwargs):
            function(*args, **kwargs)
        return new_function

    def list_func(function):
        def new_function(self, items, *args, **kwargs):
            x = None
            console.info("Select item by index:")

            for i,j in enumerate(items):
                if j.endswith(".dat (Denied)"):
                    console.custom(INFO, i, " ", ERROR, j)
                else:
                    console.custom(INFO, i, " ", LOG, j)

            while True:
                ind = prompt()
                try:
                    x = int(ind.raw.strip())
                    console.info("Selected: " + items[x])
                    break
                except (IndexError, ValueError):
                    pass

                if self.int._cmd_check(ind):
                    return

                console.error("Invalid index")


            return function(self, items, x, *args, **kwargs)

        return new_function

    def yn(self, question):
        while True:
            console.custom(LOG, question, INFO, "[Y/N]", LOG, ": ", end="")
            x = console.log.input()

            if x.lower().strip() in ["yes", "y", "ye", "yeah", "accept", "success"]:
                return True

            if x.lower().strip() in ["no", "n", "nien", "denied", "declined"]:
                return False

    @response
    def help(self):
        console.info("Commands:")
        console.log(" help                      Exit Program")
        console.log(" exit                      Exit Program")
        console.log(" add                       Add file to encryption base")
        console.log(" list                      List encrypted files")
        console.log(" chpass                    Change password")
        console.log(" drive                     Get current drive (directory files are being stored in)")
        console.log(" chdrive                   Change the drive being used")

    @response
    def notexist(self, file):
        console.warn("Could not find: '%s'"%file)

    @response
    def encrypt_file(self, file):
        console.success("File encrypted: '%s'"%file)

    @list_func
    def operations(self, items, index):
        return index

    @response
    @list_func
    def list_select(self, items, index):
        opt = self.operations(["Decrypt", "Remove", "Rename", "Preview", "View data"])
        filename = x = os.path.join(self.int.drive.get_drive(), "data", self.int.master_key.encrypt(      encrypter.File.pad(str(items[index]).encode())).hex() + ".dat")
        if opt == 0:
            self.int.master_key.update_iv(b'\xff'*16)
            f = encrypter.File(filename)
            new_file = os.path.join(self.int.drive.get_drive(), str(items[index]))
            f.decrypt_file(self.int.master_key, new_file)
            console.success("Decrypted as: %s"%new_file)
        elif opt == 1:
            console.warn("[WARNING] You are about perminatly delete '%s'?"%x)
            if self.yn("Are you sure u want to continue?"):
                os.remove(filename)
        elif opt == 2:
            new_name = console.log.input("New name:")
            self.int.master_key.update_iv(b'\xff'*16)
            new_name = os.path.join(self.int.drive.get_drive(), "data", self.int.master_key.encrypt(      encrypter.File.pad(new_name.encode())).hex() + ".dat")

            os.rename(filename, new_name)
            console.success("Renamed '%s' to '%s'."%(filename, new_name))

        elif opt == 3:
            f = encrypter.File(filename)
            data = f.read_raw(self.int.master_key)[0:1024]
            console.info("==============BEGIN PREVIEW=============")
            try:
                console.log(data.decode())
            except UnicodeDecodeError:
                console.log(data.hex())
            console.info("==============END PREVIEW=============")

        elif opt == 4:
            console.warn("[WARNING] This may couse a crash with large files!")
            if self.yn("Are you sure u want to dump the full filedata to console?"):
                f = encrypter.File(filename)
                data = f.read_raw(self.int.master_key)
                console.info("==============BEGIN PREVIEW=============")
                try:
                    console.log(data.decode())
                except UnicodeDecodeError:
                    console.log(data.hex())
                console.info("==============END PREVIEW=============")






class interpreter:
    def __init__(self, drive, master_key, config):
        super().__init__()
        self.active = True
        self.drive = drive
        self.config = config
        self.master_key = master_key
        self.r = res(self)

    def path(path):
        return path.strip().replace("'", "").replace('"', "")

    def _cmd_check(self, inp):
        if inp.raw.strip() == "":
            pass

        elif inp.iscmd("help", "?"):
            self.r.help()

        elif inp.iscmd("exit", "kill"):
            exit()

        elif inp.iscmd("setdrive", "chdrive"):
            p = interpreter.path(inp.argsraw)
            if os.path.isdir(p):
                self.config.update("drive", p)
                console.success("Setdrive to: '%s'"%p)
                console.log("Reloading...")
                self.active = False
            else:
                self.r.notexist(p)

        elif inp.iscmd("getdrive", "drive"):
            console.log("Current drive is: '%s'"%self.drive.drive)

        elif inp.iscmd("add"):
            p = interpreter.path(os.path.join(inp.raw[4::].strip()))
            if os.path.isfile(p):
                f = encrypter.File(p)
                self.master_key.update_iv(b'\xff'*16)
                x = os.path.join(self.drive.get_drive(), "data", self.master_key.encrypt(      encrypter.File.pad(str(f).encode())).hex() + ".dat")
                f.encrypt_file(self.master_key, x)
                self.r.encrypt_file(x)
            else:
                self.r.notexist(p)

        elif inp.iscmd("list", "ls"):
            x = []
            self.master_key.update_iv(b'\xff'*16)
            for i in os.listdir(os.path.join(self.drive.get_drive(), "data")):
                try:
                    x.append(self.master_key.decrypt(encrypter.File.pad(bytes.fromhex(i.split(".")[0]))).decode().strip())
                except UnicodeDecodeError:
                    x.append("%s (Denied)"%i)

            x.sort()

            self.r.list_select(x)

        elif inp.iscmd("changepassword", "changepass", "chpassword", "chpass"):
            f = encrypter.KeyFile(self.drive)
            self.master_key = encrypter.verify(f)

            console.warn("[WARNING] You are about to change you master encryption key!")
            if self.r.yn("Are you sure u want to proceed?"):
                key1 = iigetpass("New ")
                key2 = iigetpass("Confirm ")

                if key1 == key2:
                    result = f._set_key(  encrypter.Key(hashlib.sha256(key1.encode()).digest())  , bytes.fromhex(f.get_key(self.master_key.user_key))  )
                    if result:
                        console.success("Successfully changes password")
                    else:
                        console.error("I suffered a fatal issue")
                else:
                    console.error("Passwords do not match!")
                    console.custom("")
        else:
            return False
        return True

    def start(self):
        self.r.help()
        while self.active:
            inp = prompt()

            self._cmd_check(inp)



if __name__ == '__main__':

    c = config("config.json")

    while True:
        try:
            i = interpreter(*encrypter.main(c))
            i.start()
            del i
        except FileNotFoundError:
            console.info("Select directory:")
            x = ""
            while not os.path.isdir(x):
                x = interpreter.path(prompt().raw)

            c.update("drive", x)
