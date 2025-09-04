# A simple bad word detector that can catch obfuscated versions of a few common bad words.

import re

# =========================
# 0) NORMALIZATION
# =========================

# For the case when individual characters are replaced with similar-looking digits/symbols
LEET_MAP = [
    (r'@', 'a'), (r'4', 'a'),
    (r'0', 'o'),
    (r'1', 'i'), (r'!', 'i'), (r'\|', 'i'),
    (r'3', 'e'),
    (r'5', 's'), (r'\$', 's'),
    (r'7', 't'), (r'\+', 't'),
    (r'8', 'b'),
    (r'2', 'z'),
    (r'9', 'g'),
    (r'vv', 'w'),
    (r'v', 'u'),
]

#normalizes text by making it lowercase, removing unecessary characters, replacing leetspeak, and collapsing repeated characters
def normalize(text: str) -> str:
    s = text.lower()
    s = re.sub(r'[^a-z0-9@$\+\!\|\-]', '', s)
    for pat, rep in LEET_MAP:
        s = re.sub(pat, rep, s)
    s = re.sub(r'(.)\1{1,}', r'\1', s)
    return s

# =========================
# 1) CONTEXT-SENSITIVE G2P
# =========================
# When similar linguistic clusters are used as a replacement for clusters within a bad word 

G2P_RULES = [
    (re.compile(r'tch'),   'CH'),
    (re.compile(r'ch'),    'CH'),
    (re.compile(r'sh'),    'SH'),
    (re.compile(r'ph'),    'F'),
    (re.compile(r'th'),    'TH'),
    (re.compile(r'qu'),    'KW'),
    (re.compile(r'ck'),    'K'),

    (re.compile(r'c(?=[eiy])'), 'S'),
    (re.compile(r'c'),          'K'),

    (re.compile(r'g(?=[eiy])'), 'J'),
    (re.compile(r'g'),          'G'),

    (re.compile(r'x'),   'KS'),

    (re.compile(r'j'), 'J'),
    (re.compile(r'z'), 'S'),
    (re.compile(r's'), 'S'),
    (re.compile(r'q'), 'K'),
    (re.compile(r'k'), 'K'),
    (re.compile(r'f'), 'F'),
    (re.compile(r'v'), 'V'),
    (re.compile(r'p'), 'P'),
    (re.compile(r'b'), 'B'),
    (re.compile(r'd'), 'D'),
    (re.compile(r't'), 'T'),
    (re.compile(r'm'), 'M'),
    (re.compile(r'n'), 'N'),
    (re.compile(r'r'), 'R'),
    (re.compile(r'l'), 'L'),
    (re.compile(r'w'), 'W'),
    (re.compile(r'h'), ''),     
    (re.compile(r'[aeiouy]'), 'A'),
    (re.compile(r'.'), ''),
]

# This function scans through the word and converts sequences to the clusters we saw earlier, and if a match is found, it adds its token from above
def g2p_tokens(s: str) -> list[str]:
    i, out = 0, []
    while i < len(s):
        ## I assume more things like below would be added for other edge cases, this is just for how "x" sounds like a "z" at the start of certain words. 
        ## There definetly is a better way to do this, this is what I came up with for now
        if s[i] == 'x' and i == 0:
            out.append('Z')
            i += 1
            continue
        piece = s[i:]
        emitted = False
        for pat, tok in G2P_RULES:
            m = pat.match(piece)
            if m:
                if tok:
                    out.append(tok)
                i += len(m.group(0))
                emitted = True
                break
        if not emitted:
            i += 1
    collapsed = []
    for t in out:
        if not collapsed or collapsed[-1] != t:
            collapsed.append(t)
    return collapsed

# =========================
# 2) PHONOTACTIC GATE
# =========================

#Looks at a data set of letters that are commonly found next to each other in english words, then counts how many sequences
# within the word arent in the data set. This helps the program not flag gibberish 

ALLOWED_BIGRAMS = {
    ('S','P'), ('S','T'), ('S','K'), ('S','M'), ('S','N'), ('S','L'), ('S','W'),
    ('T','R'), ('D','R'), ('K','R'), ('G','R'), ('B','R'), ('P','R'), ('F','R'),
    ('K','L'), ('G','L'), ('B','L'), ('P','L'), ('F','L'),
    ('T','W'), ('D','W'), ('K','W'), ('G','W'),
    ('T','H'), ('S','H'), ('C','H'), ('S','R'),
    ('K','S'), ('K','T'), ('K','R'), ('K','L'),
    ('P','T'), ('P','S'),
    ('N','D'), ('N','T'), ('N','S'), ('M','P'),
    ('R','N'), ('R','L'), ('R','S'),
    ('A','K'), ('A','S'), ('A','N'), ('A','R'), ('A','L'), ('A','M'), ('A','T'),
    ('A','D'), ('A','F'), ('A','V'), ('A','B'), ('A','P'), ('A','G'), ('A','J'),
    ('A','CH'), ('A','SH'), ('A','TH'),
    ('CH','A'), ('SH','A'), ('TH','A'), ('J','A'), ('G','A'), ('K','A'), ('S','A'),
    ('R','A'), ('L','A'), ('M','A'), ('N','A'), ('P','A'), ('B','A'), ('F','A'),
    ('V','A'),
    ('A','A'),
}

def phonotactic_violations(tokens: list[str]) -> int:
    v = 0
    for a, b in zip(tokens, tokens[1:]):
        if (a, b) not in ALLOWED_BIGRAMS:
            v += 1
    return v



# =========================
# 3) TOKEN-LEVEL DAMERAU–LEVENSHTEIN
# =========================
#Thank you geeks for geeks for teaching me how to do this! this essentially helps me flag things like pr0n = porn
# this computers the minimal amount of edits through insertion, deletion, substitution, and transposition needed to change one list of tokens into another

def damerau_lev(a: list[str], b: list[str], max_dist=1) -> int:
    la, lb = len(a), len(b)
    if abs(la - lb) > max_dist + 1:
        return max_dist + 2
    dp = [[0]*(lb+1) for _ in range(la+1)]
    for i in range(la+1): dp[i][0] = i
    for j in range(lb+1): dp[0][j] = j
    for i in range(1, la+1):
        for j in range(1, lb+1):
            cost = 0 if a[i-1] == b[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,
                dp[i][j-1] + 1,
                dp[i-1][j-1] + cost
            )
            if i > 1 and j > 1 and a[i-1] == b[j-2] and a[i-2] == b[j-1]:
                dp[i][j] = min(dp[i][j], dp[i-2][j-2] + 1)
    return dp[la][lb]

# =========================
# 4) TARGETS & MATCHING
# =========================

BAD_WORDS = {
    "sex":  "sex",
    "porn": "porn",
    "fuck": "fuck",
    "bitch":"bitch",
    "cock": "cock",
}

PER_WORD_THRESHOLDS = {
    "sex":  {"max_dist": 1, "max_violations": 1},
    "porn": {"max_dist": 1, "max_violations": 1},
    "fuck": {"max_dist": 1, "max_violations": 1},
    "bitch":{"max_dist": 1, "max_violations": 1},
    "cock": {"max_dist": 1, "max_violations": 1},
}

SURFACE_PREFILTERS = {
    "sex":  [r'x', r'ks', r'ck',],
    "fuck": [r'k', r'ck', r'kk', r'qk'],
}

TARGETS = {label: g2p_tokens(normalize(surface))
           for label, surface in BAD_WORDS.items()}

def _passes_surface_prefilter(label: str, normalized_text: str) -> bool:
    pats = SURFACE_PREFILTERS.get(label)
    if not pats:
        return True
    return any(re.search(p, normalized_text) for p in pats)
#main detector,
def contains_bad(text: str,
                 default_max_dist=1,
                 default_max_violations=1):
    """
    Returns (flagged: bool, label: str|None)
    """
    norm = normalize(text)
    tokens = g2p_tokens(norm)

    for label, tgt in TARGETS.items():
        if not _passes_surface_prefilter(label, norm):
            continue

        cfg = PER_WORD_THRESHOLDS.get(label, {})
        max_dist = cfg.get("max_dist", default_max_dist)
        max_violations = cfg.get("max_violations", default_max_violations)

        L = len(tgt)
        if L == 0:
            continue

        # Short targets: only same-length windows
        if L <= 3:
            win_lengths = {L}
        else:
            win_lengths = {L-1, L, L+1}

        for win_len in win_lengths:
            if win_len <= 0 or win_len > len(tokens):
                continue
            for i in range(0, len(tokens) - win_len + 1):
                win = tokens[i:i+win_len]
                if phonotactic_violations(win) > max_violations:
                    continue
                if damerau_lev(win, tgt, max_dist=max_dist) <= max_dist:
                    return True, label

    return False, None

# =========================
# 5) SIMPLE CLI
# =========================

if __name__ == "__main__":
    print("Type a line to check it. Press Enter on an empty line to quit.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if line == "":
            print("Bye.")
            break
        flagged, label = contains_bad(line)
        if flagged:
            print(f"Flagged. Matched bad word: {label}")
        else:
            print("Safe.")
