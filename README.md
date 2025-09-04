
# Language Filter Simulation Application

This is one of the first projects I've ever made; so I kinda just did whatever.

I wanted to fuse what I knew about CS and Linguistics, so I made an application that takes in input, and tries to detect if it is a flagged bad word within my word list.

This accounts for letter swaps, (e.g p0rn) cluster swaps, (secks), spaced out words, and misplaced letters (f u c k), or a combination of all of them, using tokens and the DAMERAU–LEVENSHTEIN method (thanks geek for geeks!)

If I were to expand this project, I'd want to use AI/ML to understand the given context the word is used, then try to deem if it is inappropriate or not. For example, words like Freak or Birch would become censored; these are common words used as replacements for a swear word but are okay in given contexts.
