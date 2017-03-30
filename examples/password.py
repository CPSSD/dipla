from os import path, system
from time import time
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

@Dipla.distributable()
def check_pw(given, words):
    from hashlib import md5
    from base64 import b64encode, b64decode
    import sys
    import bcrypt

    given = b64decode(given)
    for word in words:
        word = word.strip().encode('utf-8')
        #m = md5()
        #m.update(word.strip())
        #a = m.digest()
        a = bcrypt.hashpw(word)
        if a == given:
            return word.decode('utf-8')
    return None

url = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/10_million_password_list_top_100.txt"

system("wget '" + url + "' -O .wordlist.txt")

lines = None
with open('.wordlist.txt', 'r') as f:
    lines = [line.strip() for line in f.readlines()]
    print(lines)

def get_hashed_pw(pw):
    from hashlib import md5
    import hashlib
    from base64 import b64encode
    import bcrypt
    pw = pw.encode('utf-8')
    #m = md5()
    #m.update(pw)
    a = bcrypt.hashpw(pw)
    return a.decode('utf-8')
    return b64encode(m.digest()).decode('utf-8')

def get_random_word():
    import random
    return random.choice(lines)


secret = get_random_word()
print('cheating, secret =', secret)
given = get_hashed_pw(secret)

start = time()
ans = check_pw(given, lines)
end = time()
print(end-start)

start = time()
n = 10
partitions = [lines[i::n] for i in range(n)]
print (len(partitions)*len(partitions[0]))
print(len(lines))
print('going')
results = Dipla.apply_distributable(check_pw, [given] * n, partitions)
for word in Dipla.get(results):
    if word is not None:
        print('result =', word)
        end = time()
        print(end-start)
