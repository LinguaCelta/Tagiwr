import os
import unicodedata2
from pathlib import Path

ref_path = Path(os.path.dirname(__file__))

def isaposword(test_string):
    nonwordchar = 0
    for char in test_string:
        if not char.isalpha() and char not in ["'", "-"]:
            nonwordchar += 1
    if nonwordchar > 0:
        return False
    else:
        return True

def isword(test_string):
    return isaposword(test_string) and "'" not in test_string

def iscyword(test_string):
    nonwordchar = 0
    if not isaposword(test_string):
        return False
    else:
        for char in test_string:
            if char not in ["â", "ê", "î", "ô", "û", "ŵ", "ŷ", "ä", "ë", "ö", "ï", "é", "è", "í", "ì", "Â", "Ê", "Î", "Ô", "Û", "Ŵ", "Ŷ", "Ä", "Ë", "Ö", "Ï", "É", "È", "Í", "Ì", "-", "'"]:
                return False
        return True

def load_mut_exclusions():
    csv_file = Path(ref_path/"mut_exclude.csv")
    with open(csv_file) as mutex:
        mutfile = mutex.read()
        lines = mutfile.splitlines()
        mutex_list = set()
        for l in lines:
            bits = l.split(",")
            form = bits[0]
            mut = bits[1]
            mut_tuple = (form, mut)
            mutex_list.add(mut_tuple)
    return mutex_list

mut_exclusions = load_mut_exclusions()

mwu_exclusions = {"'slawer", "a", "ac", "adnabod", "ail", "am", "ar", "at", "beth", "bob", "byth", "diolch", "dros", "dy", "e", "ei", "eich", "ein", "eitha'", "eitha", "er", "erbyn", "ers", "eu", "fan", "fath", "fel", "fesul", "ffon", "ffonau", "ffor'", "ffor", "ffordd", "ffyn", "ffôn", "fodd", "fy", "gan", "ger", "gwaetha'r", "gwaethar", "gyda'r", "gyda", "hanner", "heb", "hollti", "hwyl", "hyd", "hynny", "i'r", "i", "man", "mewn", "mohono", "mohonoch", "mohonom", "mohonon", "mohonot", "mohonyn", "moni", "mono", "monoch", "monon", "monyn", "nag", "naill", "naw", "negesu", "negesydd", "negesyddion", "nes", "nesa", "nesaf", "newydd", "niwed", "nos", "o'r", "o", "oddi", "os", "p'un", "saith", "serch", "sglodion", "sglodyn", "shwd", "shwt", "siart", "siartiau", "slawer", "sugnydd", "sugnyddion", "sul", "sut", "swyddfa'r", "swyddfa", "swydfeydd", "synnwyr", "system", "systemau", "syth", "ta", "un", "unwaith", "uwch", "wedi'i", "wedi'r", "wrth", "wyneb", "wyth", "y", "ych", "ym", "ymlaen", "ymyriadau", "yn", "yng", "yr"}

def mutate(token):
    mutated = []
    if token[:2] == "ll":
        mutated = [(token[1:], "sm")]
    elif token[:2] == "rh":
        soft = "r" + token[2:]
        mutated = [(soft, "sm")]
    elif token[:2] == "ts":
        soft = "j" + token[2:]
        mutated = [(soft, "sm")]
    elif token[0] == "p" and token[1] not in ["h", "s"]:
        soft = "b" + token[1:]
        nasal = "mh" + token[1:]
        aspirate = "ph" + token[1:]
        mutated = [(soft, "sm"), (nasal, "nm"), (aspirate, "am")]
    elif token[0] == "t" and token[1] not in ["h", "s"]:
        soft = "d" + token[1:]
        nasal = "nh" + token[1:]
        aspirate = "th" + token[1:]
        mutated = [(soft, "sm"), (nasal, "nm"), (aspirate, "am")]        
    elif token[0] == "c" and token[1] != "h":
        soft = "g" + token[1:]
        nasal = "ngh" + token[1:]
        aspirate = "ch" + token[1:]
        mutated = [(soft, "sm"), (nasal, "nm"), (aspirate, "am")]   
    elif token[0] == "b":
        soft = "f" + token[1:]
        nasal = "m" + token[1:]
        mutated = [(soft, "sm"), (nasal, "nm")] 
    elif token[0] == "d" and token[1] != "d":
        soft = "dd" + token[1:]
        nasal = "n" + token[1:]
        mutated = [(soft, "sm"), (nasal, "nm")] 
    elif token[0] == "g":
        soft = token[1:]
        nasal = "n" + token
        mutated = [(soft, "sm"), (nasal, "nm")]
    elif token[0] == "m":
        soft = "f" + token[1:] 
        mutated = [(soft, "sm")]
    elif token[0] in ["â", "ê", "î", "ô", "ŷ", "a", "e", "i", "o", "u", "w", "y"]:
        hasp = "h" + token
        mutated = [(hasp, "hm")]
    mut_output = []
    for mut in mutated:
        if mut not in mut_exclusions:
            mut_output.append(mut)
    return mut_output


def unmutate(token):
    """ Return a list of all possible Welsh mutations of a given token """
    unmutated = []
    if len(token) > 3 and  token[:3] == "ngh":
        unmutated.append(("c{}".format(token[3:]), "nm"))
    if len(token) > 2 and  token[:2] == "ch":
        unmutated.append(("c{}".format(token[2:]), "am"))
        if token[:5] == "chyda":
            unmutated.append(("g{}".format(token[2:]), "am"))
    if len(token) > 2 and  token[:2] == "ph":
        unmutated.append(("p{}".format(token[2:]), "am"))
    if len(token) > 2 and  token[:2] == "th":
        unmutated.append(("t{}".format(token[2:]), "am"))
    if len(token) > 2 and  token[:2] == "mh":
        unmutated.append(("p{}".format(token[2:]), "nm"))
    if len(token) > 2 and token[:2] == "nh":
        unmutated.append(("t{}".format(token[2:]), "nm"))
    if len(token) > 2 and token[:2] == "ng" and token[2] != "h":
        unmutated.append(("g{}".format(token[2:]), "nm"))
    if len(token) > 1 and token[:1] == "m" and token[1] != "h":
        unmutated.append(("b{}".format(token[1:]), "nm"))
    if len(token) > 1 and  token[:1] == "n" and token[1] not in ["h", "g"]:
        unmutated.append(("d{}".format(token[1:]), "nm"))
    if len(token) > 1 and  token[:1] == "g":
        unmutated.append(("c{}".format(token[1:]), "sm"))
    if len(token) > 1 and  token[:1] == "b":
        unmutated.append(("p{}".format(token[1:]), "sm"))
    if len(token) > 1 and  token[:1] == "d" and token[1] != "d":
        unmutated.append(("t{}".format(token[1:]), "sm"))
    if len(token) > 1 and  token[:1] == "f" and token[1] != "f":
        unmutated.append(("b{}".format(token[1:]), "sm"))
        unmutated.append(("m{}".format(token[1:]), "sm"))
    if len(token) > 1 and token[:1] == "l" and not token[1] == "l":
        unmutated.append(("ll{}".format(token[1:]), "sm"))
    if len(token) > 1 and token[:1] == "r" and token[1] != "h":
        unmutated.append(("rh{}".format(token[1:]), "sm"))
    if len(token) > 2 and token[:2] == "dd":
        unmutated.append((token[1:], "sm"))
    if len(token) > 2 and token[:1] == "j":
        unmutated.append(("ts{}".format(token[1:]), "sm"))
    if len(token) > 2 and token[:2] == "ha":
        unmutated.append(("a{}".format(token[2:]), "hm"))
    if len(token) > 2 and token[:2] == "he":
        unmutated.append(("e{}".format(token[2:]), "hm"))
    if len(token) > 2 and token[:2] == "hi":
        unmutated.append(("i{}".format(token[2:]), "hm"))
    if len(token) > 2 and token[:2] == "ho":
        unmutated.append(("o{}".format(token[2:]), "hm"))
    if len(token) > 2 and token[:2] == "hu":
        unmutated.append(("u{}".format(token[2:]), "hm"))
    if len(token) > 3 and token[:2] == "hw":
        unmutated.append(("w{}".format(token[2:]), "hm"))
    if len(token) > 3 and token[:2] == "hy":
        unmutated.append(("y{}".format(token[2:]), "hm"))
    if (len(token) > 1 and token[:1] in ["a", "e", "i", "o", "u", "w", "y", "r", "l", "â", "ê", "ŵ"]) or token == "wn":
        unmutated.append(("g{}".format(token), "sm"))
    return unmutated

def deaccent(word):
    deacc = unicodedata2.normalize('NFKD', word).encode('ASCII', 'ignore').decode('ASCII')
    return [deacc]

def tag_morphology(tag):
    """ For a given (rich) POS tag, split it into a list of its morphological elements and return it """
    morphology = []
    if tag in [x[0] for x in morphological_table]:
        location = [x[0] for x in morphological_table].index(tag)
        morphology = morphological_table[location][1]
    else:
        morphology = [tag]
    return morphology
