from .reference_lists.cy_lexicon import cy_dict
from .reference_lists.en_lexicon import en_dict
from .reference_lists.gaz_lexicon import gaz_dict
from .reference_lists.cy_mwus import cy_mwus
from .reference_lists.en_mwus import en_mwus
from .reference_lists.gaz_mwus import gaz_mwus
from .reference_lists.admin_refs import *
from .reference_lists.ref_functs import *

ll_cy = set(cy_dict.keys())
ll_en = set(en_dict.keys())
ll_gaz = set(gaz_dict.keys())
ll_both = ll_cy.union(ll_en)
ll_all = ll_both.union(ll_gaz)

class Headword:
    def __init__(self, headword, language=None, en_trans=None, mutation=None):
        self._headword = headword
        self._language = language
        self._en_trans = en_trans
        self._mutation = mutation

    def word(self):
        return self._headword

    def language(self):
        return self._language

    def entries(self):
        mutation = self._mutation
        entry_list = []
        if self._en_trans != None:
            dict_items = cy_dict[self._headword]
            for di in dict_items:
                if mutation != None:
                    di["mutation"] = mutation
                if di["lemma_en"] == self._en_trans:
                    entry = Entry(self._headword, di, "cy")
                    entry_list.append(entry)
        if self._headword in ll_cy and self._language in [None, "cy"] and entry_list == []:
            dict_items = cy_dict[self._headword]
            for di in dict_items:
                if mutation != None:
                    di["mutation"] = mutation
                entry = Entry(self._headword, di, "cy")
                entry_list.append(entry)
        if self._headword in ll_en and self._language in [None, "en"] and self._en_trans == None:
            dict_items = en_dict[self._headword]
            for di in dict_items:
                if mutation != None:
                    di["mutation"] = mutation
                entry = Entry(self._headword, di, "en")
                entry_list.append(entry)
        if self._headword in ll_gaz and self._language in ["gaz", None] and self._en_trans == None:
            dict_items = gaz_dict[self._headword] 
            for di in dict_items:
                if mutation != None:
                    di["mutation"] = mutation
                entry = Entry(self._headword, di, "gaz")
                entry_list.append(entry)
        return entry_list

class MWU(Headword):
    def __init__(self, dict_item):
        self._dict_item = dict_item
        self._word = word
        self._language = language  

class Entry:
    def __init__(self, word, dict_item=None, language=None):
        self._word = word
        self._language = language
        self._dict_item = dict_item
    
    def word(self):
        return self._word

    def dict_item(self):
        return self._dict_item

    def mutation(self):
        if self._dict_item != None:
            return self._dict_item["mutation"]
        else:
            return "0m"

    def language(self):
        if self.basic_pos() == "Atd":
            return "neutral"
        else:
            if self._language in ["cy", "en"]:
                return self._language
            elif self._language == "gaz":
                return "neutral"
            elif self._language == "unk":
                return "neutral"

    def lemma(self):      
        if self._dict_item != None:
            lemma = self.dict_item()["lemma"]
        else:
            lemma = self._word
        return lemma

    def basic_pos(self):
        if self._dict_item != None:
            basic_pos = self.dict_item()["pos_basic"]
        else:
            basic_pos = "unk"
        return basic_pos

    def full_pos(self):
        if self._dict_item != None:
            full_pos = self.dict_item()["pos_enriched"]["full"]
        else:
            full_pos = "unk"
        return full_pos

    def segmented_pos(self):
        if self._dict_item != None:
            segmented_pos = self.dict_item()["pos_enriched"]["seg"]
        else:
            segmented_pos = "unk"
        return segmented_pos

    def trans(self):
        if self._dict_item != None:
            trans = self.dict_item()["lemma_en"]
        else:
            trans = self._word
        trans = trans.replace(" ", "_")
        return trans









