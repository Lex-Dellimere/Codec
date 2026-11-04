"""Checks the float formatter: every output must parse back to the same bits.
Also counts outputs longer than the shortest form (Python's repr is shortest).

    mbuild build -r && python3 tools/float_check.py build/linux/release/floatdump [count]
"""
import random, struct, subprocess, sys

def shortest_digits(x, single):
    if single:
        # Shortest digits that round to the same float32.
        for p in range(1, 18):
            s = "%.*e" % (p - 1, x)
            try:
                if struct.unpack("<f", struct.pack("<f", float(s)))[0] == x:
                    return p
            except OverflowError:
                pass
    return len(repr(abs(x)).split("e")[0].replace(".", "").lstrip("0").rstrip("0")) or 1

def digits(s):
    m = s.lstrip("-").split("e")[0].replace(".", "").lstrip("0").rstrip("0")
    return len(m) or 1

def main():
    exe = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 200000
    rng = random.Random(1)
    lines, vals = [], []
    for i in range(count):
        single = i % 4 == 3
        if single:
            b = rng.getrandbits(32)
            x = struct.unpack("<f", struct.pack("<I", b))[0]
            if x != x or x in (float("inf"), float("-inf")):
                continue
            lines.append("s%x" % b)
        else:
            b = rng.getrandbits(64) if i % 2 else struct.unpack("<Q", struct.pack("<d", rng.uniform(-1e6, 1e6)))[0]
            x = struct.unpack("<d", struct.pack("<Q", b))[0]
            if x != x or x in (float("inf"), float("-inf")):
                continue
            lines.append("%x" % b)
        vals.append((x, single))
    for x in [0.0, -0.0, 1.0, 0.1, 1e21, 1e-7, 5e-324, 1.7976931348623157e308, 2.2250738585072014e-308, 123456789012345680.0]:
        lines.append("%x" % struct.unpack("<Q", struct.pack("<d", x))[0])
        vals.append((x, False))
    out = subprocess.run([exe], input="\n".join(lines) + "\n", capture_output=True, text=True).stdout.split("\n")
    bad = longer = 0
    for (x, single), s in zip(vals, out):
        y = float(s)
        if single:
            y = struct.unpack("<f", struct.pack("<f", y))[0]
        if struct.pack("<d", y) != struct.pack("<d", x):
            bad += 1
            if bad < 10:
                print("round trip failed:", repr(x), s)
        elif digits(s) > shortest_digits(x, single):
            longer += 1
    print("%d values, %d failed round trip, %d not shortest" % (len(vals), bad, longer))
    sys.exit(1 if bad else 0)

main()
