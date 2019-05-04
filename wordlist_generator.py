import argparse
import re
import requests

import inflect

parser = argparse.ArgumentParser(prog="processor")
parser.add_argument("--url", "-u", action="append", default=[])
parser.add_argument("--cookie", "-c", type=str, action="append", default=[])
parser.add_argument("--prefix", type=str, action="append", default=[])
parser.add_argument("--prefix_file", type=str, default=None)
parser.add_argument("--postfix", type=str, action="append", default=[])
parser.add_argument("--postfix_file", type=str, default=None)
parser.add_argument("--join-type", choices=["normal", "camel", "hyphon", "underscore"], default="underscore")
parser.add_argument("--wordlist", "-w", type=str, default=None)
args = parser.parse_args()

def join_words(*args, join_type="underscore"):
    if join_type == "normal":
        return "".join(args)
    elif join_type == "camel":
        return args[0].lower() + "".join(x.capitalize() for x in args[1:])
    elif join_type == "hyphon":
        return "-".join(args)
    return "_".join(args)

cookies = {}
for cookie in args.cookie:
    name, value = cookie.split("=", 1)
    cookies[name] = value

prefixes = args.prefix
if args.prefix_file is not None:
    with open(args.prefix_file) as f:
        prefixes.extend(f.read().splitlines())

postfixes = args.postfix
if args.postfix_file is not None:
    with open(args.postfix_file) as f:
        postfixes.extend(f.read().splitlines())

data = ""
for url in args.url:
    r = requests.get(url, cookies=cookies)
    data += r.text
wordset = set(re.findall(r'\b[A-Za-z]+\b', data))

if args.wordlist is not None:
    with open(args.wordlist) as f:
        wordset.update(f.read().splitlines())

e = inflect.engine()
for word in list(wordset):
    _words = [word, word.lower(), word.capitalize(), e.plural(word), e.singular_noun(word), e.present_participle(word)]
    for _word in [x for x in _words if isinstance(x, str)]:
        if len(prefixes):
            _words.extend([join_words(prefix, _word, join_type=args.type) for prefix in prefixes])
        if len(postfixes):
            _words.extend([join_words(_word, postfix, join_type=args.type) for postfix in postfixes])
        if len(prefixes) and len(postfixes):
            _words.extend([join_words(prefix, _word, postfix, join_type=args.type) for postfix in postfixes for prefix in prefixes])
    wordset.update(_words)

for x in sorted(x for x in wordset if isinstance(x, str)):
    print(x)
