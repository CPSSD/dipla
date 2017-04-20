from os import path
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

# This program finds the word with the most vowels from the opening of the Communist Manifesto

communist_manifesto = """
 A spectre is haunting Europe — the spectre of communism. All the powers of old Europe have entered into a holy alliance to exorcise this spectre: Pope and Tsar, Metternich and Guizot, French Radicals and German police-spies.

Where is the party in opposition that has not been decried as communistic by its opponents in power? Where is the opposition that has not hurled back the branding reproach of communism, against the more advanced opposition parties, as well as against its reactionary adversaries?

Two things result from this fact:

I. Communism is already acknowledged by all European powers to be itself a power.

II. It is high time that Communists should openly, in the face of the whole world, publish their views, their aims, their tendencies, and meet this nursery tale of the Spectre of Communism with a manifesto of the party itself.

To this end, Communists of various nationalities have assembled in London and sketched the following manifesto, to be published in the English, French, German, Italian, Flemish and Danish languages. 
"""

input_data = [word.lower() for word in communist_manifesto.split() if len(word) > 0]
print(input_data)

@Dipla.reduce_distributable(reduce_group_size=5)
def find_most_vowels(words):
    vowels = set(['a', 'e', 'i', 'o', 'u'])
    best = ""
    best_count = -1
    for word in words:
        n = 0
        for c in word:
            if c in vowels:
                n += 1
        if n > best_count:
            best_count = n
            best = word
    return best

print("input data:", input_data)

out = Dipla.apply_distributable(find_most_vowels, input_data).get()

print('result:', out)
