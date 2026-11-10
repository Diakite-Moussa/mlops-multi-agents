class _Obj:
    def __init__(self, name):
        self.object_name = name


class _Resp:
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data

    def close(self):
        pass

    def release_conn(self):
        pass


class FakeClient:
    def __init__(self):
        self.store = {}

    def put_object(self, bucket, key, data, length, content_type=None):
        self.store[(bucket, key)] = data.read()

    def get_object(self, bucket, key):
        return _Resp(self.store[(bucket, key)])

    def list_objects(self, bucket, prefix="", recursive=True):
        return [_Obj(k) for (b, k) in self.store if b == bucket and k.startswith(prefix)]

