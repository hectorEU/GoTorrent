import csv
from collections import defaultdict

mem = list(defaultdict())


def retrieve(cycle, file_name, downloaded):
    global mem
    try:
        dct = mem[cycle]
        if file_name in dct:
            dct[file_name] = (dct[file_name] + downloaded) / 2
        else:
            dct[file_name] = downloaded
    except IndexError:
        mem.append({file_name: downloaded})


def export_csv():
    with open("stats.csv", "wb") as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["cycle", "palabra", "frase", "parrafo"])
        for i, dct in enumerate(mem):
            word = dct["palabra.txt"] if "palabra.txt" in dct else 0
            sent = dct["frase.txt"] if "frase.txt" in dct else 0
            para = dct["parrafo.txt"] if "parrafo.txt" in dct else 0
            writer.writerow([str(i), str(word), str(sent), str(para)])
