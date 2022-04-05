import re
import string

class Definite:
    RE_punct = re.compile(r"[\.,:;\"\'!?\-\—<>{}\[\]()]+$")
    RE_ibang = re.compile(r"[!?]+$")
    RE_period = re.compile(r"\.+$")
    RE_mid = re.compile(r"[,;:—]+$")
    RE_open = re.compile(r"[<{\[(]+$")
    RE_close = re.compile(r"[>}\])]+$")
    RE_quote = re.compile(r"^[\'\"]+$")
    RE_symbol = re.compile(r"[^\s^.,:;!?\-\—\'\"<>{}\[\]()^\w]")
    RE_number1 = re.compile(r"^\d+\.?\d+?%")
    RE_number2 = re.compile(r"^-?[0-9\.,]+$")
    RE_decades = re.compile(r"^\d\d\d0au%")
    RE_decades_short = re.compile(r"^\d0au%")
    
    def __init__(self, word_object, pos=None):
        self._word = word_object.word()
        self._cat = word_object.category()
        self._pos = pos

    def word(self):
        return self._word

    def non_alpha_pos(self, word):
        pos = None
        if self._cat in ["hashtag", "email", "url", "username", "moji"]:
            pos = {"cat":"Gw", "other_type":"ann", "full":"Gwann", "seg":"Gw ann"}
        elif self._cat == "mwu":
            return None
        elif self._cat == "Ep":
            pos = {"cat":"E", "prop":"p", "full":"Ep", "seg":"E p"}
        if re.match(Definite.RE_punct, self._word):
            if re.match(Definite.RE_ibang, self._word):
                pos = {"cat":"Atd", "punct_type":"t", "full":"Atdt", "seg":"Atd t"}
            if re.match(Definite.RE_period, self._word):
                pos = {"cat":"Atd", "punct_type":"t", "full":"Atdt", "seg":"Atd t"}
            if re.match(Definite.RE_mid, self._word):
                pos = {"cat":"Atd", "punct_type":"can", "full":"Atdcan", "seg":"Atd can"}
            if re.match(Definite.RE_open, self._word):
                pos = {"cat":"Atd", "punct_type":"chw", "full":"Atdchw", "seg":"Atd chw"}
            if re.match(Definite.RE_close, self._word):
                pos = {"cat":"Atd", "punct_type":"de", "full":"Atdde", "seg":"Atd de"}
            if self._word == "-":
                pos = {"cat":"Atd", "punct_type":"cys", "full":"Atdcys", "seg":"Atd cys"}
            if re.match(Definite.RE_quote, self._word):
                pos = {"cat":"Atd", "punct_type":"dyf", "full":"Atddyf", "seg":"Atd dyf"}
        elif re.match(Definite.RE_symbol, self._word):
            pos = {"cat":"Gw", "other_type":"sym", "full":"Gwsym", "seg":"Gw sym"}
        elif re.match(Definite.RE_number1, self._word):
            pos = {"cat":"Gw", "other_type":"dig", "full":"Gwdig", "seg":"Gw dig"}
        elif re.match(Definite.RE_number2, self._word):
            pos = {"cat":"Gw", "other_type":"dig", "full":"Gwdig", "seg":"Gw dig"}
        elif re.match(Definite.RE_decades, self._word):
            pos = {"cat":"E", "gender": "g", "number": "ll", "full":"Egll", "seg":"E g ll"}
        elif re.match(Definite.RE_decades_short, self._word):
            pos = {"cat":"E", "gender": "g", "number": "ll", "full":"Egll", "seg":"E g ll"}
        else:
            not_alpha = 0
            for char in word:
                if not char.isalpha():
                    not_alpha += 1
                if char in ["-", "'"]:
                    not_alpha -= 1
            if not_alpha != 0:
                pos = {"cat":"Gw", "other_type":"sym", "full":"Gwsym", "seg":"Gw sym"}
        return pos

    def abbreviation_pos(self, word):
        pos = None
        if self._word.lower() in ["html", "url", "http", "https", "bbc", "s4c", "wjec", "cbac", "uk", "usa", "ussr", "uda", "itv"]:
            pos = {"cat":"Gw", "other_type":"acr", "full":"Gwacr", "seg":"Gw acr"}
        return pos

    def non_welsh_pos(self, word):
        pos = None
        non_welsh = 0
        for char in self._word:
            if ord(char) > ord('z'):
                if char not in ["â", "ê", "î", "ô", "û", "ŵ", "ŷ", "ä", "ë", "ö", "ï", "é", "è", "í", "ì", "Â", "Ê", "Î", "Ô", "Û", "Ŵ", "Ŷ", "Ä", "Ë", "Ö", "Ï", "É", "È", "Í", "Ì"]:
                    non_welsh += 1
        if non_welsh > 0:
            pos = {"cat":"Gw", "other_type":"est", "full":"Gwest", "seg":"Gw est"}
        return pos

    def def_pos(self):
        pos = self.non_alpha_pos(self._word)
        if pos == None:
            pos = self.abbreviation_pos(self._word)
        if pos == None:
            pos = self.non_welsh_pos(self._word)
        return pos


class CorCenCC_cleaned:
    ## pre-processes corcencc text to deal with transcriber codes and other common metadata ##
    saib = re.compile(r" ?</? ?[sS]aib ?> ?")
    noise_start = re.compile(r" *<N> *")
    noise_end = re.compile(r" *</N> *")
    noise_spaces = re.compile(r"(\[~[^ ~]+) ([^~]+~\])")
    anon_spaces = re.compile(r"(<anon>[^ <]+) ([^<]+</anon>)")
    anon_start = re.compile(r" ?<anon ?> *")
    anon_end = re.compile(r" *</anon> ?")

    anon_pair = re.compile(r"(<anon>[^ <]+) ([^<]+</anon>)")
    eng_pi1 = re.compile(r" ?<eng?> *")
    eng_pi2 = re.compile(r" *</eng?> ?")
    eng_pi3 = re.compile(r" ?<eng? gair=")
    punct = re.compile(r"([\?\!\.,\:\;\'\"])</en>")
    en1 = re.compile(r"<en([^>]*)> ?(\w+)(\W+) ?</en>")
    en2 = re.compile(r"<en[^>]*>[^<]+ [^<]+</en>")
    en3 = re.compile(r"(<en[^>]*>[^<]+[^<]+</en>)")
    en4 = re.compile(r"<en[^>]*>[^<]+ [^<]+</en>")
    en5 = re.compile(r"(?:</?en(?:gair=[A-Za-z]+)?>| )")
    
    @classmethod
    def cleaned(cls, input_text):
        output = ""
        input_text = input_text.replace("​", "")
        input_text = re.sub(CorCenCC_cleaned.saib, r" \[~saib~\] ", input_text)
        input_text = re.sub(CorCenCC_cleaned.noise_start, " [~", input_text)
        input_text = re.sub(CorCenCC_cleaned.noise_end, "~] ", input_text)
        while CorCenCC_cleaned.noise_spaces.findall(input_text) != []:
            input_text = re.sub(r"(\[~[^ ~]+) ([^~]+~\])", r"\1_\2", input_text)
        input_text = re.sub(CorCenCC_cleaned.anon_start, r" <anon>", input_text)
        input_text = re.sub(CorCenCC_cleaned.anon_end, r"</anon> ", input_text)
        while CorCenCC_cleaned.anon_spaces.findall(input_text) != []:
            input_text = re.sub(CorCenCC_cleaned.anon_pair, r"\1_\2", input_text)
        input_text = input_text.replace("<anon>", "[##")
        input_text = input_text.replace("</anon>", "##]")
        input_text = re.sub(CorCenCC_cleaned.eng_pi1, r" <en>", input_text)
        input_text = re.sub(CorCenCC_cleaned.eng_pi2, r"</en> ", input_text)
        input_text = re.sub(CorCenCC_cleaned.eng_pi3, r" <en:gair=", input_text)
        input_text = re.sub(CorCenCC_cleaned.punct, r"</en> \1", input_text)
        input_text = re.sub(CorCenCC_cleaned.en1, r"<en\1>\2</en> \3", input_text)
        if re.search(CorCenCC_cleaned.en2, input_text) != None:
            input_split = re.split(CorCenCC_cleaned.en3, input_text)
            output_split = []
            for split in list(filter(None, input_split)):
                if re.match(CorCenCC_cleaned.en4, split):
                    words = list(filter(None, re.split(CorCenCC_cleaned.en5, split)))
                    for word in words:
                        if not word.isalpha():
                            output_split.append(word)
                        else:
                            out = "<en>" + word + "</en>"
                            output_split.append(out)
                else:
                    output_split.append(split)
            output = re.sub(r"  +", " ", " ".join(output_split))
        else:
            output = input_text
        return output


