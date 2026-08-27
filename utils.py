import random
import string

def generate_username(length, allow_digits, allow_uppercase):
 
    chars = string.ascii_lowercase
    if allow_uppercase:
        chars += string.ascii_uppercase
    if allow_digits:
        chars += string.digits
    chars += '_'

    first_pool = string.ascii_lowercase
    if allow_uppercase:
        first_pool += string.ascii_uppercase

    while True:
        username = random.SystemRandom().choice(first_pool)
        for i in range(length - 1):
            while True:
                ch = random.SystemRandom().choice(chars)
                if not (username[-1] == '_' and ch == '_'):
                    break
            username += ch
        if not username.endswith('_'):
            return username

def is_liquid_username(username):
  
    if not (4 <= len(username) <= 5):
        return False
    if not username.isalpha():
        return False
    if not username.islower():
        return False
    return True
