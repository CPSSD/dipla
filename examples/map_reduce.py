from os.path import abspath
import sys
sys.path.append(abspath('../dipla'))
from dipla.api import Dipla


def generate_urls():
    base_url = '/home/brandon/.webpages/euler/problem={}'
    number_of_urls = 585
    for i in range(number_of_urls):
        yield base_url.format(i + 1)


@Dipla.distributable()
def count_word_on_web_page(url):
    try:
        import bs4 as bs
        import re
        file = open(url, 'rt')
        raw_page = file.read()
        file.close()
        soup = bs.BeautifulSoup(raw_page, 'html.parser')
        pattern = re.compile('primes'.lower())
        all_matches = pattern.findall(soup.text.lower())
        answer = len(all_matches) if all_matches is not None else 0
        return answer
    except Exception as e:
        print(e)


def main():
    word_count_promise = Dipla.apply_distributable(
        count_word_on_web_page,
        generate_urls()
    )
    word_counts = [int(s) for s in Dipla.get(word_count_promise)]
    total_word_count = sum(word_counts)
    print(total_word_count)


if __name__ == '__main__':
    main()
