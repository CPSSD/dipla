import random
from os import path, system
from time import time
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

@Dipla.distributable()
def check_pw(given, words, salt):
    from base64 import b64decode
    import sys
    import bcrypt

    ops = [
        lambda s: s,
        lambda s: s.upper(),
        lambda s: s.capitalize(),
        lambda s: s+'!',
        lambda s: s.replace('o', '0'),
        lambda s: s.replace('a', '4'),
        lambda s: s.replace('e', '3'),
        lambda s: s.replace('i', '1'),
        lambda s: s.replace('l', '1'),
        lambda s: s+'1',
    ]

    salt = b64decode(salt.encode('utf-8'))
    for orig_word in words:
        orig_word = orig_word.strip()
        for op in ops:
            word = op(orig_word).encode('utf-8')
            a = bcrypt.hashpw(word, salt).decode('utf-8')
            if a == given:
                Dipla.terminate_tasks()
                return word.decode('utf-8')
    return None


# download the wordlist to .wordlist, and load into list
url = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/10_million_password_list_top_1000.txt"
system("wget '" + url + "' -O .wordlist.txt 2> /dev/null")
lines = None
with open('.wordlist.txt', 'r') as f:
    lines = [line.strip() for line in f.readlines()[:25]]

def get_hashed_pw(pw):
    # return (hashed_password, salt)
    from base64 import b64encode
    import bcrypt

    salt = bcrypt.gensalt()
    pw = pw.encode('utf-8')
    a = bcrypt.hashpw(pw, salt)
    return a.decode('utf-8'), b64encode(salt).decode('utf-8')

def get_random_word():
    return random.choice(lines)


ops = [
    lambda s: s,
    lambda s: s.upper(),
    lambda s: s.capitalize(),
    lambda s: s+'!',
    lambda s: s.replace('o', '0'),
    lambda s: s.replace('a', '4'),
    lambda s: s.replace('e', '3'),
    lambda s: s.replace('i', '1'),
    lambda s: s.replace('l', '1'),
    lambda s: s+'1',
]
secret = random.choice(ops)(get_random_word())
given, salt = get_hashed_pw(secret)
print('cheating, secret =', secret, ', hashed =', given, ', salt =', salt)

start = time()
for line in lines:
    ans = check_pw(given, [line], salt)
end = time()
print(end-start, 'seconds locally')
print('partitioning')
start = time()
n = len(lines)
partitions = [lines[i::n] for i in range(n)]
print(partitions)
results = Dipla.apply_distributable(check_pw, [given] * n, partitions, [salt] * n)
print('sending')

for result in Dipla.get(results):
    if result:
        print('result =', result)
        end = time()
        print(end-start, 'seconds distributed')
