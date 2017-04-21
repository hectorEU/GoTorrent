import csv
from collections import defaultdict

mem = list(defaultdict())


def retrieve(cycle, file_name, percent):
    global mem
    try:
        dct = mem[cycle]
        if file_name in dct:
            dct[file_name] = (dct[file_name] + percent) / 2
        else:
            dct[file_name] = percent
    except IndexError:
        mem.append({file_name: percent})


def export_csv():
    with open('eggs.csv', 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['Spam'] * 5 + ['Baked Beans'])
        spamwriter.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])
    with open("stats.csv", "wb") as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["cycle", "palabra", "frase", "parrafo"])
        for i, dct in enumerate(mem):
            word = dct["palabra.txt"] if "palabra.txt" in dct else 0
            sent = dct["frase.txt"] if "frase.txt" in dct else 0
            para = dct["parrafo.txt"] if "parrafo.txt" in dct else 0
            writer.writerow([str(i), word, sent, para])
