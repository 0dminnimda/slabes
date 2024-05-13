import sys

def to_base(x, b):
    out = []
    while x:
        x, r = divmod(x, b)
        out.append(r)
    return out[::-1]


ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def to_base_str(x, b, alpha=ALPHA):
    return "".join(alpha[it] for it in to_base(x, b)) or "0"


if __name__ == "__main__":
    print("Type in your numbers and upon exit program will convert them all")
    lines = []
    try:
        for line in sys.stdin:
            lines.append(line)
    except:
        for line in lines:
            print(to_base_str(int(line), 32))
