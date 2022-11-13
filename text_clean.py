from curses.ascii import isascii, isdigit


WIKI_FILE: str = "frwiktionary-20221001-all-titles-in-ns0"
PASSPHRASE_WORDS_COUNT = 7
# Enforce a reasonable maximum length for passphrases to avoid DoS
MAX_PASSPHRASE_LENGTH = 128

contains_underscore = lambda word: True if "_" in word else False
contains_dash = lambda word: True if "-" in word else False

def is_ascii(s: str):
    return all(ord(c) < 128 for c in s)

def contains_number(s: str):
    for ch in s:
        if isdigit(ch):
            return True

    return False

def all_eq(s: str):
    for i in range(0, len(s)-1, 1):
        if s[i] != s[i+1]:
            return False

    return True


def read_lines(file_name: str) -> list:
    lines: list = []

    with open(file_name) as f:
        for line in f:
            line = line.strip().lower()

            if all_eq(line) or contains_number(line) or not line.isalpha():
                continue
            
            if "_" in line or "-" in line or "." in line or "\'" in line:
                continue
            
            if (len(line) * PASSPHRASE_WORDS_COUNT + PASSPHRASE_WORDS_COUNT) > MAX_PASSPHRASE_LENGTH:
                continue
            
            if is_ascii(line):
                lines.append(line)

    return lines 

if __name__ == "__main__":
    lines = read_lines(WIKI_FILE)

    with open("output.txt", "w") as fw:
        for line in lines:
            fw.write(f"{line}\n")
