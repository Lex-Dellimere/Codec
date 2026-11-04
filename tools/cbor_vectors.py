"""Writes tests/data/cbor_vectors.txt from the RFC 8949 Appendix A examples.

Input: appendix_a.json from https://github.com/cbor/test-vectors (the
Appendix A examples as hex). Each output line is: hex, TAB, expected dump,
TAB, 1 if the writer must reproduce the bytes exactly (preferred
serialization) else 0. The dump format matches cbor_dump in
tests/cbor_test.mettle; this file holds its own small decoder for it.

    python3 tools/cbor_vectors.py path/to/appendix_a.json
"""
import json, struct, sys

def dump(b, i):
    ib = b[i]; i += 1
    major, ai = ib >> 5, ib & 31
    if ai < 24: arg = ai
    elif ai == 24: arg = b[i]; i += 1
    elif ai == 25: arg = int.from_bytes(b[i:i+2], "big"); i += 2
    elif ai == 26: arg = int.from_bytes(b[i:i+4], "big"); i += 4
    elif ai == 27: arg = int.from_bytes(b[i:i+8], "big"); i += 8
    else: arg = None
    if major == 0: return "u%d" % arg, i
    if major == 1: return "n%d" % arg, i
    if major in (2, 3):
        p = "b" if major == 2 else "s"
        if arg is None:
            out = b""
            while b[i] != 0xff:
                s, i = dump(b, i)
                out += bytes.fromhex(s[1:])
            return "_" + p + out.hex(), i + 1
        return p + b[i:i+arg].hex(), i + arg
    if major in (4, 5):
        items = []
        n = arg if arg is not None else -1
        k = 0
        while (n < 0 and b[i] != 0xff) or k < n:
            if major == 4:
                s, i = dump(b, i)
            else:
                ks, i = dump(b, i)
                vs, i = dump(b, i)
                s = ks + ":" + vs
            items.append(s); k += 1
        if n < 0: i += 1
        o, c = ("[", "]") if major == 4 else ("{", "}")
        return ("_" if n < 0 else "") + o + ",".join(items) + c, i
    if major == 6:
        s, i = dump(b, i)
        return "t%d(%s)" % (arg, s), i
    if ai == 20: return "false", i
    if ai == 21: return "true", i
    if ai == 22: return "null", i
    if ai == 23: return "undefined", i
    if ai in (25, 26, 27):
        if ai == 25:
            f = struct.unpack(">e", arg.to_bytes(2, "big"))[0]; w = 2
            bits = struct.unpack(">Q", struct.pack(">d", f))[0]
            if f != f:  # NaN: keep the payload as Codec widens it
                bits = 0x7ff0000000000000 | ((arg & 0x3ff) << 42) | ((arg & 0x8000) << 48)
        elif ai == 26:
            f = struct.unpack(">f", arg.to_bytes(4, "big"))[0]; w = 4
            bits = struct.unpack(">Q", struct.pack(">d", f))[0]
        else:
            w = 8; bits = arg
        return "f%d:%016x" % (w, bits), i
    return "x%d" % arg, i

def main():
    vectors = json.load(open(sys.argv[1]))
    lines = []
    for v in vectors:
        if v["hex"] == "f818":
            continue  # simple(24): from RFC 7049; RFC 8949 section 3.3 makes it not well-formed
        b = bytes.fromhex(v["hex"])
        s, end = dump(b, 0)
        assert end == len(b), v
        lines.append("%s\t%s\t%d" % (v["hex"], s, 1 if v["roundtrip"] else 0))
    open("tests/data/cbor_vectors.txt", "w").write("\n".join(lines) + "\n")
    print(len(lines), "vectors")

main()
