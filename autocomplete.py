import pandas as pd
import time

word = "plu"

words = pd.read_csv("words.csv")
words = words.values.flatten().tolist()
def autocomplete(word, words):
    word = list(word)
    counter = 0
    for i in words:
        for j in range(len(word)):
            if word[j] == i[j]:
                counter += 1
                continue
            else:
                break
        if counter == len(word):
            print(i)
        counter = 0
autocomplete(word, words)