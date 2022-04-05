import re
import string
import shutil
import subprocess
import os
import unicodedata2
from termcolor import colored
from .reference import *
from .preprocessor import *

both_mwus = set(cy_mwus.keys()).intersection(set(en_mwus.keys()))
all_mwus = both_mwus.intersection(set(gaz_mwus.keys()))

REGEX = {
    "para": re.compile(r'\n+'),
    "engair": re.compile(r'<en:gair="([ A-Za-z\'\-]+)"> ?([^<]+)</en>'),
    "anons": re.compile(r'\[##([^<]+)##\]'),
    "repeats": re.compile(r'([\w]*?)(\w)\2+([\w]*)'),
    "wordchars": re.compile(r"([^\W\d_]+)", re.UNICODE),
    "pattern": re.compile(r"(?<=[.|!|?])(?<!\s[A-Z][.])(?<![A-Z][.][A-Z][.])(?<![.]\s[.])(?<![.][.])[\s]"),
    "space": re.compile(r"\s"),
    "en_split": re.compile(r"(<en[^>]*>[^<]*</en>)"),
    "code_split": re.compile(r"(\[##[^<]*##\])"),
    "speaker_split": re.compile(r"(\[~[^~]*~\])"),
    "stars": re.compile(r"(\[\*[^\*]*\*\])"),
    "quotes": re.compile(r"(''+)"),
    "hyphens": re.compile(r"(\-)+"),
    "unders": re.compile(r"(_)+"),
    "nwchar": re.compile(r"(\W)"),
    "nwcharseq": re.compile(r"(\W+)"),
    "digitseq": re.compile(r"(\d+)")
    }

class Text:
    def __init__(self, text, file_name, text_id, language=None, preproc="n"):
        self._text = text
        self._language = language
        self._filename = file_name
        self._text_id = text_id
        self._preproc = preproc

    def text(self):
        """ Returns the entire text."""
        return self._text

    def id(self):
        return self._text_id

    def language(self):
        """ Returns the language of this text, or None if it's unknown. """
        return self._language

    def filename(self):
        return self._filename

    def paragraphs(self):
        para_objs = []
        para_list = re.split(REGEX["para"], self._text)
        para_list = list(filter(None, para_list))
        for para in para_list:
            p_obj = Paragraph(para, self._filename, self._text_id, self._preproc)
            para_objs.append(p_obj)
        return para_objs

class Paragraph:
    def __init__(self, para_text, file_name, text_id, preproc):
        self._filename = file_name
        self._text_id = text_id
        self._text = para_text
        self._preproc = preproc

    def filename(self):
        return self._filename

    def genre(self):
        return self._filename[:3]

    def id(self):
        return self._text_id

    def sentence_raw(self):
        first_split = re.split(REGEX["pattern"], self._text)
        sentences = list(filter(None, first_split))
        k = 0
        split_sentences = []
        while k < len(sentences):
            # If an empty sentence is encountered, discard it
            if sentences[k] != "":
                current = sentences[k].strip()
                # treat ellipsis as sentence-ending punctuation
                if current.find("...") != -1:
                    ellipsis = current.find("...")
                    part1 = current[:ellipsis+3].strip()
                    part2 = current[ellipsis+4:].strip()
                    split_sentences.append(part1)
                    split_sentences.append(part2)

                else:
                    split_sentences.append(current)
                k+=1
        return split_sentences

    def sentences(self):
        split_sentences = self.sentence_raw()
        clean_split = []
        output = []
        for rawsent in split_sentences:
            if self._preproc == "y":
                # This step is specifically aimed at processing CorCenCC's data, and is only used if the flag -p is invoked on the command line.
                preprocessed = CorCenCC_cleaned.cleaned(rawsent)
                clean_split.append(preprocessed)
            else:
                clean_split.append(rawsent)
        for i, sent in enumerate(clean_split):
            sent_obj = Sentence(sent, self.id(), self._filename)
            output += [sent_obj]
        return output

    def cg_output(self, cg_readings):
        """ Given a set of CG-formatted readings, run VISL CG-3 """
        vislcg3_location = shutil.which("vislcg3")
        cg_process = subprocess.Popen([vislcg3_location, '--soft-limit', '45', '--hard-limit', "100", "-B", "-v", '0', '-g', '{}/grammar/cy_grammar_2021'.format(os.path.dirname(os.path.abspath(__file__)))], stdin=subprocess.PIPE,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cg_output, cg_error = cg_process.communicate(input=cg_readings.encode("utf-8"))
        if b"Grammar could not be parsed" in cg_error:
            err_msg = cg_error.decode("utf-8")
            msg = colored("There is a problem with the constraint grammar!\nPlease fix before rerunning the code.", attrs=['reverse', 'bold'])
            out_msg = "\n\n{}\n\n{}".format(msg, err_msg)
            raise RuntimeError(out_msg)
        else:
            return cg_output.decode("utf-8")

    def cg_output_trace(self, cg_readings):
        """ Given a set of CG-formatted readings, run VISL CG-3 with trace turned on"""
        vislcg3_location = shutil.which("vislcg3")
        cg_process = subprocess.Popen([vislcg3_location, '--soft-limit', '45', '--hard-limit', "100", "--trace", "-B", "-v", '0', '-g', '{}/grammar/cy_grammar_2021'.format(os.path.dirname(os.path.abspath(__file__)))], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        cg_output = cg_process.communicate(input=cg_readings.encode("utf-8"))[0]
        return cg_output.decode("utf-8")

    def tsv_output(self, cg_readings, file_id):
        cg_result = list(filter(None, cg_readings.splitlines()))
        tsv_formatted = {}
        item_count = 0
        curr_tok = ""
        tsv_items = ""
        for cg_item in cg_result:
            if cg_item[0] != "\t":
                curr_tok = cg_item[2:-2].replace("_'", "'")
                if curr_tok == "literal_backslash":
                    curr_tok = "\\"
                elif curr_tok == "literal_dbl_quot":
                    curr_tok = '"'
                tsv_formatted[str(item_count)] = {}
                tsv_formatted[str(item_count)]["token"] = curr_tok
                tsv_formatted[str(item_count)]["readings"] = []
                tsv_formatted[str(item_count)]["multiple"] = False
                item_count += 1

            else:
                tsv_formatted[str(item_count-1)]["readings"].append([cg_item[1:]])
                if len(tsv_formatted[str(item_count-1)]["readings"]) < 1:
                    tsv_formatted[str(item_count)]["multiple"] = True  
        sentence_counter = 0  
        word_counter = 0    
        for item in tsv_formatted:
            banmedd = 0 
            for reading in tsv_formatted[item]["readings"]:
                if "Ban medd 3 b u" in reading[0] or "Ban medd 3 g u" in reading[0]:
                    banmedd += 1
            if banmedd == 2:
                new_readings = []
                for i, rd in enumerate(tsv_formatted[item]["readings"]):
                    if "Ban medd 3 b u" in rd[0]:
                        new_readings += [[rd[0].replace("Ban medd 3 b u", "Ban medd 3 d u")]]
                    elif "Ban medd 3 g u" not in rd[0]:
                        new_readings += [[rd[0]]]
                tsv_formatted[item]["readings"] = new_readings
            readings = []
            token = tsv_formatted[item]["token"]
            tsv_reading = []
            for reading in tsv_formatted[item]["readings"]:
                bits = reading[0].split(" ")
                lemma = bits[0][1:-1]
                if lemma == "literal_backslash":
                    lemma = "\\"
                elif lemma == "literal_dbl_quot":
                    lemma = '"'
                sentence_index = bits[-1][2:-2]
                if sentence_index == sentence_counter:
                    word_counter += 1
                else:
                    sentence_counter = sentence_index
                    word_counter = 1
                position = "{},{}".format(sentence_counter,word_counter)
                language = bits[1][1:-1]
                if len(set(lemma)) > 1:
                    lemma = lemma.replace("_", " ")
                    token = token.replace("_", " ")
                basic_pos = bits[2]
                full_pos = basic_pos + "".join(bits[3:-3])
                if full_pos == "":
                    full_pos = basic_pos
                mutation = bits[-2][1:]
                if tsv_reading == []:
                    tsv_reading = [position, lemma, language, basic_pos, full_pos, mutation]
                else:
                    tsv_reading[1] += "|{}".format(lemma)
                    tsv_reading[2] += "|{}".format(language)
                    tsv_reading[3] += "|{}".format(basic_pos)
                    tsv_reading[4] += "|{}".format(full_pos)
                    tsv_reading[5] += "|{}".format(mutation)
            tsv_line = self.genre() + file_id + "\t" + token + "\t" + "\t".join(tsv_reading) + "\n"
            tsv_items += tsv_line
        return tsv_items



class Sentence:
    def __init__(self, sent, text_id, filename, language=None):
        self._sent = sent
        self._language = language
        self._filename = filename

    def sentence_text(self):
        return self._sent

    def position(self):
        return self._position

    def language(self):
        return self._language

    def words(self):
        """splits the sentence on whitespace and punctuation"""
        """ Normalize different kinds of potential apostrophe/single quotation and dash/hyphen characters """
        word_list = []
        sent_nbsp = self._sent.replace(" ", " ")
        sent_apos = (re.sub(r"[’‘`´]", "'", sent_nbsp))
        sent_quot = (re.sub(r"[“”]", '"', sent_apos))
        sentence = (re.sub(r"[‑—–]", "-", sent_quot))
        sentence = sentence.replace("><", "> <")
        circ_replace = {"â":"â", "ê":"ê", "î":"î", "ô":"ô", "û":"û", "ŷ":"ŷ", "ŵ":"ŵ"}
        for char in circ_replace:
            if char in sentence:
                sentence = sentence.replace(char, circ_replace[char])
        split = list(filter(None, re.split(REGEX["space"], sentence)))
        split_list = []
        for sl in split:
            if sl.find("<en") != -1:
                if sl.count("<en") == sl.count("</en>"):
                    split_list += list(filter(None, re.split(REGEX["en_split"], sl)))
                else:
                    detag = (re.sub(r"</?en[^>]*>", "", sl))
                    split_list.append(detag)
            elif sl.find("[##") != -1:
                if sl.count("[##") == sl.count("##]"):
                    split_list += list(filter(None, re.split(REGEX["code_split"], sl)))
                else:
                    detag = (re.sub(r"(\[##|##\])", "", sl))
                    split_list.append(detag)
            elif sl.find("[~") != -1 or sl.count("~]") != -1:
                if sl.count("[~") == sl.count("~]"):
                    split_list += list(filter(None, re.split(REGEX["speaker_split"], sl)))
                else:
                    detag = (re.sub(r"(\[~|~\])", "", sl))
                    split_list.append(detag)
            elif sl.find("[*") != -1 or sl.count("*]") != -1:
                if sl.count("[*") == sl.count("*]"):
                    split_list += list(filter(None, re.split(REGEX["stars"], sl)))
                else:
                    detag = (re.sub(r"(\[\*|\*\])", "", sl))
                    split_list.append(detag)
            elif sl != "":
                split_list.append(sl)
        for sl in split_list:
            if sl.find("<en") != -1:
                word = Word(sl, category="en_tagged")
                word_list += [word]
            elif sl.find("[##") != -1:
                word = Word(sl, category="anon")
                word_list += [word]
            elif sl.find("[~") != -1:
                word = Word(sl, category="transcription_code")
                word_list += [word]
            elif sl.find("[*") != -1:
                word = Word(sl, category="transcription_code")
                word_list += [word]
            elif sl.isalpha():
                word = Word(sl, category="alpha")
                word_list += [word]
            elif sl in ll_all:
                word = Word(sl)
                word_list += [word]
            elif "''" in sl:
                sl_spl = re.split(REGEX["quotes"], sl)
                for slsp in sl_spl:
                    if set(slsp) != "'":
                        slsp_string = WordString(slsp)
                        word_list += slsp_string.punct_split()
                    else:
                        slsp_word = Word(slsp, category="punct")
                        word_list += [slsp_word]
            elif sl not in ["", " "]:
                sl_string = WordString(sl)
                word_list += sl_string.punct_split()
        word_list = list(filter(None, word_list))
        word_list = self.mwus(word_list)
        return word_list

    def tokens(self):
        word_list = []
        token_list = []
        for word in self.words():
            if word.word() not in ["", " "]:
                split_tokens = word.token_split()
                for split_t in split_tokens:
                    st = split_t[0]
                    cat = split_t[1]
                    word_list.append((st, cat))
        for i, tok in enumerate(word_list):
            word_obj = Word(tok[0], category=tok[1])
            token = Token(word_obj)
            token_list.append(token)
        return token_list

    def mwus(self, word_list):
        mwu_list = []
        list_len = len(word_list)
        count_len = len(word_list)
        item = 0
        while count_len > 0:
            wf = word_list[item].word().lower()
            words = []
            if item < list_len and (wf in cy_mwus):
                max_len = cy_mwus[wf]
                if item + max_len > list_len:
                    max_len = len(word_list[item:])
                words.append(wf)
                limit = item+max_len
                word_slice = word_list[item+1:limit]
                for ws in word_slice:
                    words.append(ws.word())
                mwu_word = ""
                while len(words) > 1:
                    mwu = "_".join(words)
                    if mwu in ll_cy:
                        mwu_word = mwu
                        break
                    else:
                        words = words[:-1]
                if mwu_word == "":
                    mwu_list.append(word_list[item])
                else:
                    mwu_list.append(Word(mwu_word))
                count_len -= len(words)
                item += len(words)
            else:
                mwu_list.append(word_list[item])
                count_len -= 1
                item += 1
        return mwu_list

    def unknowns(self):
        unknown_list = []
        for tok in self.tokens():
            if len(tok.entries()) == 1 and tok.entries()[0].basic_pos() == "unk":
                unknown_list.append(tok.entries()[0].word())
        return unknown_list

    def cg_input(self, sentence_index):
        cg_input = ""
        for tok in self.tokens():
            cg_input += tok.cg_formatted(sentence_index)
        return cg_input

class Word:
    """ The word class. """
    def __init__(self, word, category=None, language=None):
        self._word = word
        self._language = language
        self._category = category

    def word(self):
        """ Returns the text content of this word."""
        return self._word

    def normalized(self):
        return self.word().lower()

    def language(self):
        """ Returns the language of this word, or None if it's unknown. """
        return self._language

    def category(self):
        return self._category

    def hyphenation(self, item):
        hyphenated = item
        cat = self._category
        if item.find("-") != -1 and self._category not in ["en_tagged", "anon", "transcription_code", "username", "url", "email", "hashtag", "moji"] and not item in ll_all:  
            hyph = item.index("-")
            if item[:hyph].lower() in ll_gaz and item[hyph+1:].lower() in ll_gaz:
                hyphenated = [item]
                cat = "Ep"
            elif item[:hyph+1].lower() in ll_all and item[hyph+1:].lower() in ll_all:
                hyphenated = [item[:hyph+1].lower(), item[hyph+1:].lower()]
            else:
                hyphenated = re.split(REGEX["hyphens"], item)
                hyphenated = list(filter(None, hyphenated))
                cat = None
        elif item.find("_") != -1 and self._category not in ["en_tagged", "anon", "transcription_code", "username", "url", "email", "hashtag", "moji"]:  
            underscore = item.index("_")
            if item in ll_all:
                hyphenated = [item]
                cat = "mwu"
            else:
                hyphenated = re.split(REGEX["unders"], item)
                hyphenated = list(filter(None, hyphenated))
                cat = None
        else:
            hyphenated = [item]
        return (hyphenated, cat)

    def token_split(self):
        tokens = []
        word = self._word
        wd_info = self.hyphenation(word)
        wd_list = wd_info[0]
        wd_cat = wd_info[1]
        for w in wd_list:
            tokens.append((w, wd_cat))
        return tokens

class Token(Word):
    """ The tokens class. Tokens are words with a part of speech, variant forms, and (where available) information about associated dictionary entries."""
    
    def __init__(self, word, language=None):
        super().__init__(word, language)
        self._word_obj = word
        self._word = word.word()
        #self._token_position = token_position

    def word(self):
        """ Returns the original wordform upon which the token is based"""
        en_cleaned = re.sub(r'</?en[^>]*>', '', self._word)
        anon_cleaned = re.sub(r'(\[##|##\])', '', en_cleaned)
        return anon_cleaned

    def word_obj(self):
        return self._word_obj

    def sentence_no(self):
        return self._sentence_no

    def cg_formatted(self, sentence_i):
        sentence_index = '"{' + str(sentence_i) + '}"'
        if self._word in ["\\", '"']:
            if self._word == "\\":
                self_alias = "literal_backslash"
            else:
                self_alias = "literal_dbl_quot"
            cg_text = '"<{}>"\n'.format(self_alias)
            for entry in self.entries():
                entry_line = '\t"{}"\t[{}]\t{}\t:{}:\t{}\t{}\n'.format(self_alias, entry.language(), entry.segmented_pos(), self_alias, "+0m", sentence_index)
                cg_text += entry_line
        elif "\\" in self._word:
            self_alias = self._word.replace("\\", "\\\\")
            cg_text = '"<{}>"\n'.format(self_alias)
            for entry in self.entries():
                entry_line = '\t"{}"\t[{}]\t{}\t:{}:\t{}\t{}\n'.format(self_alias, entry.language(), entry.segmented_pos(), self_alias, "+0m", sentence_index)
                cg_text += entry_line
        else:
            wordobj = self._word_obj
            if wordobj.category() == "anon":
                cg_text = '"<[{}]>"\n'.format(self.word())
            else:
                cg_text = '"<{}>"\n'.format(self.word())
            for entry in self.entries():
                if entry.mutation() == None:
                    mutation = "\t+0m"
                else:
                    mutation = "\t+" + entry.mutation()
                entry_line = '\t"{}"\t[{}]\t{}\t:{}:\t{}\t{}\n'.format(entry.lemma(),entry.language(), entry.segmented_pos(), entry.trans(), mutation, sentence_index)
                cg_text += entry_line
        return cg_text

    def variants(self):
        variants = Variants(self.word()).variants()
        return variants
    def nonstandard(self):
        if "nonstandard" in self.variants():
           return self.variants()["nonstandard"]
        else:
            return []
    def elision(self):
        if "elision" in self.variants():
           return self.variants()["elision"]
        else:
            return []
    def spellcheck(self):
        if "spellcheck" in self.variants():
           return self.variants()["spellcheck"]
        else:
            return []
    def dehyphenated(self):
        if "dehyph" in self.variants():
           return self.variants()["dehyph"]
        else:
            return []
    def deaccented(self):
        if "deacc" in self.variants():
            return self.variants()["deacc"]
        else:
            return []

    def entries(self):
        # Get the various dictionary entries for this token
        wordobj = self._word_obj
        wordform = self._word
        entries = []
        defpos = Definite(wordobj).def_pos()
        if wordobj.category() == "en_tagged":
            regexp = REGEX["engair"]
            regexp_match = regexp.match(wordform)
            if regexp_match:
                en_trans = regexp_match.group(1)
                tok = regexp_match.group(2)
                if tok.lower() in ll_cy:
                    cy_entries = Headword(tok.lower(), language="cy", en_trans=en_trans).entries()
                    entries += cy_entries
                else:
                    entries = [Entry(tok, dict_item=None, language="en")]
            else:
                en_word = re.sub(r'</?en( gair="[a-zA-Z\'-]+ ")?>', "", wordform)
                if en_word.lower() in ll_en:
                    en_entries = Headword(en_word.lower(), language="en").entries()
                    for ee in en_entries:
                        entries.append(ee)
                else:
                    entries = [Entry(en_word, dict_item=None, language="en")]
        elif wordobj.category() == "anon":
            regexp = REGEX["anons"]
            regexp_match = regexp.match(wordform)
            if regexp_match:
                code = regexp_match.group(1)
                if code in ("enw", "enwp", "lle", "sefydliad", "cyfenw"):
                    lemma_en = "proper_noun"
                    defpos = {"cat":"E", "prop":"p", "full":"Ep", "seg":"E p"}
                elif code == "enwb":
                    lemma_en = "proper_noun"
                    defpos = {"cat":"E", "prop":"p", "gender":"b", "full":"Epb", "seg":"E p b"}
                elif code == "enwg":
                    lemma_en = "proper_noun"
                    defpos = {"cat":"E", "prop":"p", "gender":"g", "full":"Epg", "seg":"E p g"}
                else:
                    lemma_en = "anonymized"
                    defpos = {"cat":"Anon", "full":"Anon", "seg":"Anon"}
                dict_item = {}
                anon_lemma = "[" + code + "]"
                dict_item["lemma"] = anon_lemma
                dict_item["lemma_en"] = lemma_en
                dict_item["pos_basic"] = defpos["cat"]
                dict_item["pos_enriched"] = defpos
                dict_item["mutation"] = "0m"
                entries = [Entry(anon_lemma, dict_item, language="neutral")]
            else:
                entries = [Entry(wordobj.word(), dict_item=None, language="unk")]
        elif wordobj.category() == "transcription_code":
            dict_item = {}
            dict_item["lemma"] = wordform
            dict_item["lemma_en"] = "[CorCenCC_transcription_code]"
            dict_item["pos_basic"] = "Gw"
            dict_item["pos_enriched"] = {"cat":"Gw", "other_type":"ann", "full":"Gwann", "seg":"Gw ann"}
            dict_item["mutation"] = "0m"
            entries = [Entry(wordobj.word(), dict_item, language="neutral")]
        elif defpos != None:
            if defpos["cat"] == "E" and "prop" not in defpos:
                language = "cy"
            else:
                language = "neutral"
            dict_item = {}
            dict_item["lemma"] = wordobj.normalized()
            dict_item["lemma_en"] = wordobj.normalized()
            dict_item["pos_basic"] = defpos["cat"]
            dict_item["pos_enriched"] = defpos
            dict_item["mutation"] = "0m"
            entries = [Entry(wordobj.word(), dict_item, language)]
        elif wordobj.normalized() in ll_all:
            lookup = Headword(wordobj.normalized())
            entries = lookup.entries()
        else:
            entries = self.try_variants()
        if entries == []:
            entries = [Entry(wordobj.word(), dict_item=None, language="unk")]
        return entries

    def try_variants(self, wordform=None, mut_type=None):
        wordobj = self._word_obj
        if wordform != None and wordform in ll_gaz:
            lookup = Headword(wordform, language="gaz", en_trans=None, mutation=mut_type)
            return lookup.entries()
        else:
            wordform = self._word_obj.normalized()
        entries = []
        if self.dehyphenated() != []:
            for dehyph in self.dehyphenated():
                lookup = Headword(self.dehyphenated()[0][0], language=self.dehyphenated()[0][1], en_trans=None, mutation=mut_type)
                entries += lookup.entries()
        if self.elision() != [] or self.nonstandard() != []:
            forms = self.elision() + self.nonstandard()
            for form in forms:
                lookup = Headword(form[0], language=form[1], en_trans=None, mutation=mut_type)
                entries += lookup.entries()
        if entries == [] and self.deaccented() != []:
            lookup = Headword(self.deaccented()[0][0], language=self.deaccented()[0][1], en_trans=None, mutation=mut_type)
            entries = lookup.entries()
        if entries == [] and self.spellcheck() != []:
            for form in self.spellcheck():
                lookup = Headword(form[0], language=form[1], en_trans=None, mutation=mut_type)
                entries += lookup.entries()
        if entries == [] and mut_type == None:
            if unmutate(wordform) != []:
                for um in unmutate(wordform):
                    entries += self.try_variants(wordform=um[0].lower(), mut_type=um[1])
        return entries

class Variants:
    def __init__(self, word):
        self._word = word

    def word(self):
        return self._word

    def variants(self):
        variants = {}
        if deaccent(self._word) != []:
            deacc = deaccent(self._word)[0]
            variants["deacc"] = []
            if deacc in ll_cy:
                variants["deacc"] = [(deacc, "cy")]
        if self.hyphenation() != []:
            dehyph = self.hyphenation()[0]
            variants["dehyph"] = []
            for dh in dehyph:
                if dehyph in ll_cy:
                    variants["dehyph"] += [(dehyph, "cy")]
                if dehyph in ll_en:
                    variants["dehyph"] += [(dehyph, "en")]
                if dehyph in ll_gaz:
                    variants["dehyph"] += [(dehyph, "gaz")]
        if self.elision() != []:
            variants["elision"] = []
            for elision in self.elision():
                if elision in ll_cy:
                    if "elision" in variants:
                        variants["elision"] = [(elision, "cy")]
                    else:
                        variants["elision"] += [(elision, "cy")]
        if self.nonstandard() != []:
            variants["nonstandard"] = []
            for ns in self.nonstandard():
                if ns in ll_cy:
                    if "nonstandard" in variants:
                        variants["nonstandard"] = [(ns, "cy")]
                    else:
                        variants["nonstandard"] += [(ns, "cy")]
        if self.spellcheck() != []:
            variants["spellcheck"] = []
            for sp in self.spellcheck():
                if sp in ll_cy:
                    if "spellcheck" in variants:
                        variants["spellcheck"] = [(sp, "cy")]
                    else:
                        variants["spellcheck"] += [(sp, "cy")]     
        return variants

    def hyphenation(self):
        dehyph = []
        token = self._word.lower()
        if token.find("-") != -1 and len(set(token)) > 1:
            spaces = token.replace("-", "_")
            solid = token.replace("-", "")
            dehyph += [spaces, solid]
        return dehyph

    def elision(self):
        elision_list = []
        token = self._word.lower()
        if len(token) > 3:
            if token[-1:] == "'":
                elision_list += ["{}f".format(token[:-1]), "{}r".format(token[:-1]), "{}l".format(token[:-1])]
            if token[-1:] in ["a", "e"]:
                """ Check for endings spelled with "e"/"a" instead of "au" or "ai" """
                elision_list += ["{}au".format(token[:-1]), "{}ai".format(token[:-1]), "{}ae".format(token[:-1])]
            if token[-1:] in ["a", "â", "e", "ê", "i", "î", "o", "ô", "u", "û", "w", "ŵ", "y", "ŷ"]:
                elision_list += (["{}f".format(token)])
            if token[-1:] in ["b", "c", "d", "f", "g", "h", "j", "l", "m", "n", "p", "r", "s", "t"] or token[0][-2:] in ["ch", "dd", "ff", "ng", "ll", "ph", "th"]:
                elision_list += ["{}r".format(token), "{}l".format(token)]
        return elision_list

    def nonstandard(self):
        ns_list = []
        token = self._word.lower()
        if len(token) > 4:
            if token[-2:] in ["es"]:
                ns_list += ["{}ais".format(token[:-2])]
            elif token[-3:] in ["est"]:
                ns_list += ["{}aist".format(token[:-3])]
            elif token[-3:] in ["ish"]:
                ns_list += ["{}ais".format(token[:-3])]
            elif token.rfind('e') not in [-1, 0]:
                eindex = token.rfind('e')
                if token[eindex-1] not in ["a", "e"] :
                    start = token[:eindex]
                    end = token[eindex+1:]
                    join_au = start + "au" + end
                    join_ae = start + "ae" + end
                    join_ai = start + "ai" + end    
                    ns_list += [join_au, join_ae, join_ai]
                if token[-1] == "e" and token[-2] not in ["a", "e"]:
                    end_au = token[:-1] + "au"
                    end_ae = token[:-1] + "ae"
                    end_ai = token[:-1] + "ai"
                    ns_list += [end_au, end_ae, end_ai]
            if token[-2:] in ["ar", "at", "ap", "as", "ad", "ag", "aj", "al", "ac", "ab", "an", "am"]:
                token_ea = token[:-2] + "e" + token[-1]
                ns_list += [token_ea]
            elif token[-3:] in ["ach", "all", "add", "aff", "ath"]:
                token_ea = token[:-3] + "e" + token[-2:]
                ns_list += [token_ea]
        if token.endswith("odd"):
            oedd = token[:-2] + "edd"
            ns_list += [oedd]
        if len(set(token)) < len(token)-3:
            repeats = REGEX["repeats"]
            while repeats.match(token):
                repmatch = repeats.match(token)
                token = repmatch.group(1) + repmatch.group(2) + repmatch.group(3)
            ns_list += [token]
        return ns_list

    def spellcheck(self):
        sp_list = []
        token = self._word.lower()
        var_list = [token]
        if len(token) > 4:
            match = re.search(r"a([eiu])", token)
            if match:
                if match.group(1) == "i":
                    subs = [token.replace("ai", "ae"), token.replace("ai", "au"), token.replace("ai", "ei")]
                elif match.group(1) == "e":
                    subs = [token.replace("ae", "ai"), token.replace("ae", "au"), token.replace("ae", "ei")]
                elif match.group(1) == "u":
                    subs = [token.replace("au", "ai"), token.replace("au", "ae"), token.replace("au", "ei")]
                sp_list += subs
                var_list += subs
        for var in var_list:
            if var.endswith("u"):
                sp_list.append("{}i".format(var[:-1]))
                var_list = [token] + sp_list
        for var in var_list:
            if var.find("nn") != -1:
                single_n = var.replace("nn", "n")
                sp_list += [single_n]
        return sp_list


class WordString:
    """ Strings which may or may not constitute discrete words, with methods to analyse them and split punctuation etc."""

    def __init__(self, word_string):
        self._text = word_string

    def text(self):
        return self._text
    
    def punct_split(self):
        middle = self._text
        head = ""
        tail = ""
        word_list = []
        if len(middle) > 1:
            # look for the matches to hashtags, email, etc. which are defined in the admin_refs file            
            if re.search(hashtag, middle) != None:
                h_split = list(filter(None, re.split(hashtag, middle)))
                for hs in h_split:
                    if re.fullmatch(hashtag, hs):
                        hash_word = Word(hs, category="hashtag")
                        word_list += [hash_word]
                    else:
                        new_string = WordString(hs)
                        word_list += new_string.punct_split()
                return word_list
            
            if re.search(email, middle) != None:
                e_split = list(filter(None, re.split(email, middle)))
                for es in e_split:
                    if re.fullmatch(email, es):
                        email_word = Word(es, category="email")
                        word_list += [email_word]
                    else:
                        new_string = WordString(es)
                        word_list += new_string.punct_split()
                return word_list
            
            if re.search(url, middle) != None:
                u_split = list(filter(None, re.split(url, middle)))
                for us in u_split:
                    if re.fullmatch(url, us):
                        url_word = Word(us, category="url")
                        word_list += [url_word]
                    else:
                        new_string = WordString(us)
                        word_list += new_string.punct_split()
                return word_list
            
            if re.search(username, middle) != None:
                un_split = list(filter(None, re.split(username, middle)))
                for uns in un_split:
                    if re.fullmatch(username, uns):
                        un_word = Word(uns, category="username")
                        word_list += [un_word]
                    else:
                        new_string = WordString(uns)
                        word_list += new_string.punct_split()
                return word_list

            moji_search = re.findall(moji_regex, middle)
            if len(moji_search) != 0:
                moji_split = middle.split(moji_search[0], 1)
                if moji_split[0] in ["", " "] and moji_split[1] in ["", " "]:
                    word = Word(moji_search[0], "moji")
                    word_list += [word]
                elif moji_split[0] == "":
                    word = Word(moji_search[0], "moji")
                    word_list += [word]
                    new_string = WordString(moji_split[1])
                    word_list += new_string.punct_split()
                elif moji_split[1] == "":
                    new_string = WordString(moji_split[0])
                    word_list += new_string.punct_split()
                    word = Word(moji_search[0], "moji")
                    word_list += [word]
                else:
                    new_string_head = WordString(moji_split[0])
                    word_list += new_string_head.punct_split()
                    word = Word(moji_search[0], "moji")
                    word_list += [word]
                    new_string_tail = WordString(moji_split[1])
                    word_list += new_string_tail.punct_split()
                return word_list
            if middle[0] in string.punctuation and middle[0] != "'":
                head += middle[0]
                middle = middle[1:]
                while len(middle) != 0 and middle[0] == head[-1]:
                    head += middle[0]
                    middle = middle[1:]
                if len(middle) != 0:
                    word_list = [Word(head, "punct")]
                    midword = WordString(middle)
                    word_list += midword.punct_split()
                else:
                    word = Word(middle, "punct")
                    word_list += [word]
                    return word_list
            if middle[-1] in string.punctuation and middle[-1] != "'":
                tail += middle[-1]
                middle = middle[:-1]
                while len(middle) != 0 and middle[-1] == tail[0]:
                    tail = middle[-1] + tail
                    middle = middle[:-1]
                if len(middle) != 0:
                    word_list = [Word(head, "punct")]
                    midword = WordString(middle)
                    word_list += midword.punct_split()
                else:
                    word = Word(middle, "punct")
                    word_list += [word]
                    return word_list
            if len(middle) > 1 and middle.find("'") != -1:
                middle_words = self.apos_split(middle)
            elif isword(middle):
                mid_word = Word(middle)
                middle_words = [mid_word]
            elif len(head) > 0 and len(tail) > 0 and len(middle) == 0:
                word = Word(self._text)
                word_list += [word]
            else:
                middle_words = []
                wordchars = REGEX["wordchars"]
                resplit = re.split(wordchars, middle)
                middle_units = list(filter(None, resplit))
                for mu in middle_units:
                    mu_word = Word(mu)
                    middle_words += [mu_word]
            if len(head) > 0:
                h_word = Word(head, category="punct")
                head_words = [h_word]
            else:
                head_words = []
            if len(tail) > 0:
                t_word = Word(tail, category="punct")
                tail_words = [t_word]
            else:
                tail_words = []
            word_list = head_words + middle_words + tail_words
        else:
            word = Word(middle)
            word_list += [word]
        word_list = list(filter(None, word_list))
        return word_list

    def apos_split(self, input_text):
        word_list = []
        middle = input_text
        head = ""
        tail = ""
        apos = middle.find("'")
        if middle[-2:].lower() in ("'r", "'n", "'i", "'s", "'m", "'u", "'w", "'d"):
            word_list = [Word(middle[:-2]), Word(middle[-2:])]
            word_list = list(filter(None, word_list))
            return word_list
        elif middle[-3:].lower() in ("'re", "'ch", "'th", "'ll", "'ve"):
            word_list = [Word(middle[0:apos]), Word(middle[apos:])]
            word_list = list(filter(None, word_list))
            return word_list
        elif middle[:apos+1] == "f'":
            word_list = [Word(middle[:apos+1]), Word(middle[apos+1:])]
            word_list = list(filter(None, word_list))
            return word_list
        if middle.lower() in ll_all:
            word_list = [Word(middle)]
            word_list = list(filter(None, word_list))
            return word_list
        if middle[0] == "'" and middle[1].isalpha():
            # starts with apos, and following character is alphabetic - <'di...>, <'wedi'>, etc.
            if middle.find("'", 1) == -1:
                # there are no other apos characters in this string - process using the head/tail logic below
                while not middle[-1].isalpha():
                    tail = middle[-1] + tail
                    middle = middle[:-1]
                if middle == input_text or middle not in ll_all:
                    head = middle[0]
                    middle = middle[1:]
                if middle == "":
                    middle = input_text
            else:
                # there's at least one more apos character in the string - lookup the individual parts and add to word list one at a time
                next_apos = middle.index("'", 1)
                front = middle[:next_apos]
                back = middle[next_apos:]
                if front in ll_all:
                    word = Word(front)
                    word_list += [word]
                elif front[1:].isalpha():
                    word0 = Word(front[0], category="punct")
                    word1 = Word(front[1:])
                    word_list += [word0, word1]
                    output_string = ""
                    for wl in word_list:
                        output_string += wl.word()
                        output_string += ";"
                else:
                    word = Word(front[0], category="punct")
                    word_list += [word]
                    parts = re.split(REGEX["digitseq"], front[1:])
                    more_parts = []
                    for p in parts:
                        more = re.split(REGEX["nwcharseq"], p)
                        more_parts += more
                    for mp in more_parts:
                        mp_word = Word(mp)
                        word_list += [mp_word]
                if back in ll_all:
                    word = Word(back)
                    word_list += [word]
                elif back[1:] in ll_all:
                    word0 = Word(front[0], category="punct")
                    word1 = Word(front[1:]) 
                    word_list += [word0, word1]

                else:
                    while back.find("'", 1) != -1:
                        nextest_apos = back.index("'", 1)
                        if back[:nextest_apos] in ll_all:
                            word = Word(back[:nextest_apos])
                            word_list += [word]
                            back = back[nextest_apos:]
                        elif back[1:nextest_apos] in ll_all:
                            word0 = Word(back[0], category="punct")
                            word1 = Word(back[1::nextest_apos])
                            word_list += [word0, word1]
                            back = back[nextest_apos:]
                        else:
                            word = Word(back[0], category="punct")
                            word_list += [word]
                            parts = re.split(REGEX["digitseq"], back[1:nextest_apos])
                            more_parts = []
                            for p in parts:
                                more = re.split(REGEX["nwcharseq"], p)
                                more_parts += more
                            for mp in more_parts:
                                mp_word = Word(mp)
                                word_list += [mp_word]
                            back = back[nextest_apos:]
                    if back != "":
                        if back in ll_all:
                            word = Word(back)
                            word_list += [word]
                        elif back[1:] in ll_all:
                            word0 = Word(back[0], category="punct")
                            word1 = Word(back[1:])
                            word_list += [word0, word1]
                        else:
                            word = Word(back[0], category="punct")
                            word_list += [word]
                            parts = re.split(REGEX["digitseq"], back[1:])
                            more_parts = []
                            for p in parts:
                                more = re.split(REGEX["nwcharseq"], p)
                                more_parts += more
                            for mp in more_parts:
                                mp_word = Word(mp)
                                word_list += [mp_word]
                middle = ""
        elif middle[-1] == "'" and middle[-2].isalpha() and middle[0] != "'":
            # ends with apos, and preceding character is alphabetic - <...f'>, <gair'>, etc.
            
            if middle.find("'", 0, -2) == -1: 
            # there are no other apos characters in this string - process using the head/tail logic below
                while not middle[0].isalpha():
                    head += middle[0]
                    middle = middle[1:]
                
                if middle == input_text or middle not in ll_all:
                    tail = middle[-1]
                    middle = middle[0:-1]
                
                if middle == "":
                    middle = input_text
            else:
                # there's at least one more apos character in the string - lookup the individual parts and add to word list one at a time
                parts = middle[:-1].split("'")
                apos_consumed = 1
                    # ^^ is there a preceding apos available?
                while len(parts) > 0:
                    curr_part = parts[0]
                    if apos_consumed == 0:
                        pre_apos = "'" + curr_part
                        post_apos = curr_part + "'"
                        if curr_part in ll_all:
                            # more likely to be a word with quotes on either side, since all parts other than the first are surrounded by "'"
                            word0 = Word("'", category="punct")
                            word1 = Word(curr_part)
                            word_list += [word0, word1]
                            apos_consumed = 0
                            parts = parts[1:]
                        elif pre_apos in ll_all:
                            word = Word(pre_apos)
                            word_list += [word]
                            parts = parts[2:]
                            apos_consumed = 0
                        elif post_apos in ll_all:
                            word0 = Word("'", category="punct")
                            word1 = Word(post_apos)
                            word_list += [word0, word1]
                            parts = parts[1:]
                            apos_consumed = 1
                        else:
                            word0 = Word("'", category="punct")
                            word_list += [word0]
                            split_curr = re.split(REGEX["digitseq"], curr_part)
                            more_parts = []
                            for sc in split_curr:
                                more = re.split(REGEX["nwchar"], sc)
                                more_parts += more
                            for mp in more_parts:
                                mp_word = Word(mp)
                                word_list += [mp_word]
                            parts = parts[1:]
                            apos_consumed = 0
                    else:
                        post_apos = curr_part + "'"
                        if curr_part in ll_all:
                            word0 = Word("'", category="punct")
                            word1 = Word(curr_part)
                            word_list += [word0, word1]
                            apos_consumed = 0
                            parts = parts[1:]
                        elif post_apos in ll_all:
                            word0 = Word("'", category="punct")
                            word1 = Word(post_apos)
                            word_list += [word0, word1]
                            parts = parts[1:]
                            apos_consumed = 1
                        else:
                            split_curr = re.split(REGEX["digitseq"], curr_part)
                            more_parts = []
                            for sc in split_curr:
                                more = re.split(REGEX["nwchar"], sc)
                                more_parts += more
                            for mp in more_parts:
                                mp_word = Word(mp)
                                word_list += [mp_word]
                            parts = parts[1:]
                            apos_consumed = 0
                if apos_consumed == 0:
                    word = Word("'", category="punct")
                    word_list += [word]
                middle = ""
        else:
            head_list = []
            tail_list = []
            if middle[0] == "'":
                head_word = Word("'", category="punct")
                head_list += [head_word]
                middle = middle[1:]
            if middle[-1] == "'":
                tail_word = Word("'", category="punct")
                tail_list += [tail_word]
                middle = middle[:-1]
            mid_string = WordString(middle)
            if mid_string._text == middle:
                mid_list = [Word(middle)]
            else:
                mid_list = mid_string.punct_split()
            word_list = head_list + mid_list + tail_list
            middle = ""
        if middle == input_text:     
            word = Word(input_text)
            word_list += [word]
        elif middle != "":
            if head != "":
                head_word = Word(head)
                word_list += [head_word]
            mid_word = Word(middle)
            word_list += [mid_word]
            if tail != "":
                tail_word = Word(tail)
                word_list += [tail_word]
        return word_list
