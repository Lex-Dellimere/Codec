"""Turns the msgpack-test-suite JSON into tests/data/msgpack_suite.txt.

Each output line is: expected dump, TAB, an encoding in hex, TAB, the
canonical (smallest) re-encoding in hex. The dump format matches mp_dump in
tests/msgpack_test.mettle. Needs the Python msgpack package.

    python3 tools/msgpack_suite.py
"""
import json, struct, msgpack

SRC = "tests/data/msgpack-test-suite/msgpack-test-suite.json"
OUT = "tests/data/msgpack_suite.txt"

def num(x):
    if isinstance(x, int) or (isinstance(x, float) and x.is_integer() and -2**63 <= x < 2**63):
        return str(int(x))
    return "f" + struct.pack(">d", x).hex()

def dump(v):
    if v is None: return "nil"
    if v is True: return "true"
    if v is False: return "false"
    if isinstance(v, (int, float)): return num(v)
    if isinstance(v, str): return "s" + v.encode().hex()
    if isinstance(v, bytes): return "b" + v.hex()
    if isinstance(v, list): return "[" + ",".join(dump(x) for x in v) + "]"
    if isinstance(v, dict): return "{" + ",".join(dump(k) + ":" + dump(x) for k, x in v.items()) + "}"
    if isinstance(v, msgpack.Timestamp): return "t%d:%d" % (v.seconds, v.nanoseconds)
    if isinstance(v, msgpack.ExtType): return "e%d:%s" % (v.code, v.data.hex())
    raise TypeError(v)

def main():
    suite = json.load(open(SRC))
    lines = []
    for group in suite.values():
        for case in group:
            for enc in case["msgpack"]:
                raw = bytes.fromhex(enc.replace("-", ""))
                v = msgpack.unpackb(raw, raw=False, strict_map_key=False)
                if "bignum" in case and isinstance(v, float) and v != int(case["bignum"]):
                    continue  # a float that cannot hold the exact integer
                if "binary" in case:
                    v = bytes(v)
                canon = raw.hex() if raw[0] == 0xca else msgpack.packb(v).hex()
                lines.append("%s\t%s\t%s" % (dump(v), raw.hex(), canon))
    open(OUT, "w").write("\n".join(lines) + "\n")
    print(len(lines), "lines")

main()
