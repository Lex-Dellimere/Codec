"""Reference numbers for bench/main.mettle from Python's C-backed libraries:
protobuf (upb), msgpack (C extension) and json (C encoder), on the same
messages. Needs protoc (for a descriptor set), protobuf and msgpack.

    python3 tools/bench_ref.py PATH/TO/protoc
"""
import json, subprocess, sys, tempfile, time, os
import msgpack
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

def rate(what, size, fn, n=200000):
    t = time.perf_counter()
    for _ in range(n):
        fn()
    dt = time.perf_counter() - t
    print("%s: %d MB/s, %d ns per message" % (what, size * n / dt / 1048576, dt / n * 1e9))

def main():
    protoc = sys.argv[1]
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "set.pb")
        subprocess.check_call([protoc, "-Itests/proto", "--include_imports", "--descriptor_set_out=" + out, "basic.proto"])
        fds = descriptor_pb2.FileDescriptorSet.FromString(open(out, "rb").read())
    pool = descriptor_pool.DescriptorPool()
    for f in fds.file:
        pool.Add(f)
    Person = message_factory.MessageFactory(pool).GetPrototype(pool.FindMessageTypeByName("demo.v1.Person"))
    p = Person(name="Ada Lovelace", id=1815, email="ada@analytical.engine", height=1.65, balance=-123456, active=True)
    for _ in range(4):
        p.phones.add(number="+44 20 7946 0000", type=2)
    p.scores.extend(i * 1000 for i in range(16))
    p.tags.extend(["mathematician", "writer"])
    data = p.SerializeToString()
    rate("protobuf encode (%d B)" % len(data), len(data), p.SerializeToString)
    rate("protobuf decode (%d B)" % len(data), len(data), lambda: Person.FromString(data))
    item = {"id": 123456789, "name": "widget with a fairly long name", "price": 19.99, "active": True, "tags": ["red", "large", "sale"]}
    m = msgpack.packb(item)
    rate("msgpack encode (%d B)" % len(m), len(m), lambda: msgpack.packb(item))
    rate("msgpack decode (%d B)" % len(m), len(m), lambda: msgpack.unpackb(m))
    j = json.dumps(item, separators=(",", ":"))
    rate("json write (%d B)" % len(j), len(j), lambda: json.dumps(item, separators=(",", ":")))

main()
