import json


class VertualFile():
    def __init__(self, method="t"):
        self.method = list(method)
        self.data = b'' if "b" in self.method else ""
        self.closed = False

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def check(function):
        def func(self, *args, **kwargs):
            if self.closed:
                raise ValueError("I/O operation on closed file.")
            return function(self, *args, **kwargs)
        return func

    @check
    def close(self):
        self.closed = True

    @check
    def truncate(self):
        self.data = b'' if "b" in self.method else ""

    @check
    def read(self):
        return self.data

    @check
    def write(self, data):
        self.data = self.data + data


class config:
    def __init__(self, file=":memory:", autoadd=True, create_file=True):
        self.file = file
        self.autoadd = autoadd
        self.create_file = create_file

        try:
            with self.open(self, self.file, "r") as f:
                self.raw = f.read()
        except FileNotFoundError as e:
            if self.create_file:
                self.open(self, self.file, "w").close()
            else:
                raise e

            self.raw = ""

        if self.raw.strip() == "":
            self.data = {}
        else:
            self.data = json.loads(self.raw)

    def __repr__(self):
        return self.file

    def open(self, file, *args, **kwargs):
        if str(file) == ":memory:":
            return VertualFile(*args[1::], **kwargs)
        return open(str(file), *args[1::], **kwargs)

    def update(self, key, value):
        self.data[key] = value
        self.save()

    def get(self, key, default=None):
        data = self.data.get(key, None)
        if data == None:
            if self.autoadd:
                self.data[key] = default
                self.save()
            return default
        return data


    def save(self):
        self.raw = json.dumps(self.data)
        with self.open(self, self.file, "w") as f:
            f.write(self.raw)

    def close(self):
        self.file.close()
