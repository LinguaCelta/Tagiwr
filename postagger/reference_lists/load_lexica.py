import sys
import os
import json
from termcolor import colored
from pathlib import Path

# os.path.dirname twice is a cheap and cheerful way to get the postagger directory
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__file__))

ref_path = Path(os.path.dirname(__file__))
lex_path = Path(os.path.abspath(ref_path) + "/lexica")

from admin_refs import *
from ref_functs import mutate, mwu_exclusions

def get_morph(pos):
    pose = {}
    for key in morphological_table[pos]:
    	pose[key] = morphological_table[pos][key]
    seg = ""
    keylist = list(pose)
    for part_key in pose:
        if keylist.index(part_key) != 0:
                seg += " "
        seg += pose[part_key]
    pose["seg"] = seg
    pose["full"] = pos
    return pose

def load_en():
    en_path = Path(lex_path/"en_lexicon_2021.txt")
    lexicon = {}
    mwus = {}
    with open(en_path, encoding="utf-8") as loaded_lexicon:
        entries = loaded_lexicon.read().splitlines()
        for entry in entries:
            entry_parts = entry.split("\t")
            pose = get_morph(entry_parts[4])
            if entry_parts[0] not in lexicon.keys():
                lexicon[entry_parts[0]] = [{"lemma": entry_parts[2], "lemma_en": entry_parts[1],  "pos_basic": entry_parts[3], "pos_enriched": pose, "mutation": "0m"}]
            else:
                lexicon[entry_parts[0]].append({"lemma": entry_parts[2], "lemma_en": entry_parts[1],  "pos_basic": entry_parts[3], "pos_enriched": pose, "mutation": "0m"})
        for lex_entry in lexicon:
            if lex_entry.find("_") != -1:
                bits = lex_entry.split("_")
                count = len(bits)
                keyword = bits[0]
                if keyword not in mwus or (keyword in mwus and mwus[keyword] < count):
                    mwus[keyword] = count
    return lexicon, mwus

def load_cy():
    cy_path = Path(lex_path/"cy_lexicon_2021.txt")
    lexicon = {}
    mutations = {}
    mwus = {}
    with open(cy_path, encoding="utf-8") as loaded_lexicon:
        entries = loaded_lexicon.read().splitlines()
        for entry in entries:
            entry_parts = entry.split("\t")
            wordform = entry_parts[0]
            pose = get_morph(entry_parts[4])
            if wordform not in lexicon.keys():
                lexicon[wordform] = [{"lemma": entry_parts[1], "lemma_en": entry_parts[2],  "pos_basic": entry_parts[3], "pos_enriched": pose, "mutation":"0m"}]
            else:
                lexicon[wordform].append({"lemma": entry_parts[1], "lemma_en": entry_parts[2],  "pos_basic": entry_parts[3], "pos_enriched": pose, "mutation":"0m"})
            if wordform[0] in ["l", "r", "t", "p", "c", "b", "d", "g", "m", "â", "ê", "î", "ô", "ŷ", "a", "e", "i", "o", "u", "w", "y"] and (len(wordform) > 2 or wordform in two_mut):
                mutatable = 1
                if "_" in wordform:
                    first_underscore = wordform.index("_")
                    first_word = wordform[:first_underscore]
                    if first_word in mwu_exclusions:
                        mutatable = 0
                if mutatable == 1:
                    mutated = mutate(entry_parts[0])
                    if mutated != []:
                        for mform in mutated:
                            form = mform[0]
                            mtype = mform[1]
                            if form not in lexicon:
                                lexicon[form] = [{"lemma": entry_parts[1], "lemma_en": entry_parts[2],  "pos_basic": entry_parts[3], "pos_enriched": pose, "mutation": mtype}]
                            else:
                                lexicon[form].append({"lemma": entry_parts[1], "lemma_en": entry_parts[2],  "pos_basic": entry_parts[3], "pos_enriched": pose, "mutation": mtype})
        for lex_entry in lexicon:
            if lex_entry.find("_") != -1:
                bits = lex_entry.split("_")
                count = len(bits)
                keyword = bits[0]
                if keyword not in mwus or (keyword in mwus and mwus[keyword] < count):
                    mwus[keyword] = count
    return lexicon, mwus

def load_gaz(language):
    gazetteers = {}
    term_list = []
    gaz_union = {}
    mwus = {}
    if language == "c":
        print("     casglu rhestr o dermau...")
    else:
        print("     compiling list of terms...")
    for gaz in os.listdir("{}/gazetteers".format(os.path.dirname(os.path.abspath(__file__)))):
        if gaz.startswith("._") == False: 
            with open("{}/gazetteers/{}".format(os.path.dirname(os.path.abspath(__file__)), gaz), encoding="utf-8") as loaded_gazetteer:
                terms = loaded_gazetteer.read().splitlines()
                gaz_name, gaz_ext = os.path.splitext(gaz)
                gazetteers[gaz_ext[1:]] = list(set(terms))
                term_list += terms
    term_list = set(term_list)
    if language == "c":
        message = "creu cofnodion y lecsicon"
    else:
        message = "compiling lexicon entries"
    for word in term_list:
        gaz_entry = []
        if word in gazetteers["other_proper"] or word in gazetteers["places"]:
            entry = {}
            gaz_pos = "Ep"
            lemma_en = "proper_noun"
            entry["lemma"] = word
            entry["lemma_en"] = lemma_en
            entry["pos_basic"] = "E"
            entry["pos_enriched"] = {"cat":"E", "prop": "p", "seg":"E p", "full":"Ep"}
            entry["mutation"] = "0m"
            gaz_entry += [entry]
        elif word in gazetteers["surnames"]:
            entry = {}
            gaz_pos = "Ep"
            lemma_en = "personal_name"
            entry["lemma"] = word
            entry["lemma_en"] = lemma_en
            entry["pos_basic"] = "E"
            entry["pos_enriched"] = {"cat":"E", "prop": "p", "seg":"E p", "full":"Ep"}
            entry["mutation"] = "0m"
            gaz_entry += [entry]
        elif word in gazetteers["givennames_f"] and word in gazetteers["givennames_m"]:
            entry = {}
            gaz_pos = "Ep"
            lemma_en = "personal_name"
            entry["lemma"] = word
            entry["lemma_en"] = lemma_en
            entry["pos_basic"] = "E"
            entry["pos_enriched"] = {"cat":"E", "prop": "p", "seg":"E p", "full":"Ep"}
            entry["mutation"] = "0m"
            gaz_entry += [entry]
        elif word in gazetteers["givennames_f"]:
            entry = {}
            gaz_pos = "Epb"
            lemma_en = "personal_name"
            entry["lemma"] = word
            entry["lemma_en"] = lemma_en
            entry["pos_basic"] = "E"
            entry["pos_enriched"] = {"cat":"E", "prop": "p", "gender":"b", "seg":"E p b", "full":"Epb"}
            entry["mutation"] = "0m"
            gaz_entry += [entry]
        elif word in gazetteers["givennames_m"]:
            entry = {}
            gaz_pos = "Epg"
            lemma_en = "personal_name"
            entry["lemma"] = word
            entry["lemma_en"] = lemma_en
            entry["pos_basic"] = "E"
            entry["pos_enriched"] = {"cat":"E", "prop": "p", "gender":"g", "seg":"E p g", "full":"Epg"}
            entry["mutation"] = "0m"
            gaz_entry += [entry]
        gaz_union[word] = gaz_entry

    for lex_entry in gaz_union:
        if lex_entry.find("_") != -1:
            bits = lex_entry.split("_")
            count = len(bits)
            keyword = bits[0].lower()
            if keyword not in mwus or (keyword in mwus and mwus[keyword] < count):
                mwus[keyword] = count
    return gaz_union, mwus

def check_lex():
    bad_entries_cy = []
    bad_entries_en = []
    cy_path = Path(lex_path/"cy_lexicon_2021.txt")
    en_path = Path(lex_path/"en_lexicon_2021.txt")
    with open(cy_path, encoding="utf-8") as loaded_lexicon:
        entries = loaded_lexicon.read().splitlines()
        for entry in entries:
            parts = entry.split("\t")
            if len(parts) != 5:
                bad_entries_cy.append(entry)
    with open(en_path, encoding="utf-8") as loaded_lexicon:
        entries = loaded_lexicon.read().splitlines()
        for entry in entries:
            parts = entry.split("\t")
            if len(parts) != 5:
                bad_entries_en.append(entry)
    return(bad_entries_en, bad_entries_cy)


def load_lexica(language, no_gaz=False):
    if language == "c":
        print("\nGwirio'r mewnbwn...\n\n")
    else:
        print("\nValidating input data...\n\n")
    bad_entries_en, bad_entries_cy = check_lex()
    if bad_entries_cy != [] or bad_entries_en != []:
        outcome = "fail"
        if language == "c":

            message = "Methu adeiladu'r lecsica - llinell(au) mewnbwn gwael...\n\n"
        else:
            message = "Could not build lexica - badly-formed input line(s)...\n\n"
        warning = colored(message, attrs=['reverse', 'bold'])
        print(warning)
        print("~~~~~~~ ~~~~~~~ ~~~~~~~ ~~~~~~~ ~~~~~~~ ~~~~~~~")
        if bad_entries_cy != []:
            print("******* cy_lexicon_2021.txt *******")
            for bec in bad_entries_cy:
                print(bec)
        if bad_entries_en != []:
            print("******* en_lexicon_2021.txt *******")
            for bee in bad_entries_en:
                print(bee)
        print("~~~~~~~ ~~~~~~~ ~~~~~~~ ~~~~~~~ ~~~~~~~ ~~~~~~~\n\n")
        if language == "c":
            print("Rhaid trwsio'r data gwael cyn ail-redeg y cod.")
        else:
            print("You must fix the bad data before re-running the code.")
        raise ValueError("Cannot continue until lexicon data is fixed.")
    else:
        if language == "c":
            print("Adeiladu'r lecsicon Cymraeg...")
        else:
            print("Building Welsh lexicon...")
        cy_dict_update, cmwu_update = load_cy()
        if language == "c":
            print("Adeiladu'r lecsicon Saesneg...")
        else:
            print("Building English lexicon...")
        en_dict_update, emwu_update = load_en()
        if no_gaz==False:
            if language == "c":
                print("Adeiladu lecsicon enwau priod...")
            else:
                print("Building lexicon of proper nouns...")
            gaz_dict_update, gmwu_update = load_gaz(language)
        with open(Path(ref_path/"cy_lexicon.py"), "w", encoding="utf-8") as cy_dump:
            if language == "c":
                print("Ygrifennu'r lecsicon Cymraeg i'r ffeil...")
            else:
                print("Writing Welsh lexicon to file...")
            output = "cy_dict = " + json.dumps(cy_dict_update, ensure_ascii=False)
            cy_dump.write(output)
        with open(Path(ref_path/"cy_mwus.py"), "w", encoding="utf-8") as cmwu_dump:
            output = "cy_mwus = " + json.dumps(cmwu_update, ensure_ascii=False)
            cmwu_dump.write(output)
            if language == "c":
                print("Wedi ail-adeiladu'r lecsicon Cymraeg.")
            else:
                print("Welsh lexicon rebuilt.")
        with open(Path(ref_path/"en_lexicon.py"), "w", encoding="utf-8") as en_dump:        
            if language == "c":
                print("Ygrifennu'r lecsicon Saesneg i'r ffeil...")
            else:
                print("Writing English lexicon to file...")
            output = "en_dict = " + json.dumps(en_dict_update, ensure_ascii=False)
            en_dump.write(output)
        with open(Path(ref_path/"en_mwus.py"), "w", encoding="utf-8") as emwu_dump:
            output = "en_mwus = " + json.dumps(emwu_update, ensure_ascii=False)
            emwu_dump.write(output)
            if language == "c":
                print("Wedi ail-adeiladu'r lecsicon Saesneg.")
            else:
                print("English lexicon rebuilt.")
        if no_gaz==False:
            with open(Path(ref_path/"gaz_lexicon.py"), "w", encoding="utf-8") as gaz_dump:
                if language == "c":
                    print("Ygrifennu'r lecsicon enwau priod i'r ffeil...")
                else:
                    print("Writing proper-noun lexicon to file...")
                output = "gaz_dict = " + json.dumps(gaz_dict_update, ensure_ascii=False)
                gaz_dump.write(output)
            with open(Path(ref_path/"gaz_mwus.py"), "w", encoding="utf-8") as gmwu_dump:
                output = "gaz_mwus = " + json.dumps(gmwu_update, ensure_ascii=False)
                gmwu_dump.write(output)
                if language == "c":
                    print("Wedi ail-adeiladu'r lecsicon enwau priod.")
                else:
                    print("Proper-noun lexicon rebuilt.")



