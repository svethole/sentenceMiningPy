import re
import random
import string

CLEANR = re.compile('<.*?>')

def clean_html(raw_html):
    cleantext = re.sub(CLEANR, '', raw_html)
    return cleantext

def get_random_string(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))
