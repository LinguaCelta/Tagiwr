"""
#!usr/bin/env python3
#-*- coding: utf-8 -*-
'CyTag.py'

Developed as part of the CorCenCC project (www.corcencc.org).

The original version CyTag was developed at Cardiff University 2016-2018 by Steve Neale <steveneale3000@gmail.com, NealeS2@cardiff.ac.uk>, Kevin Donnelly <kevin@dotmon.com>

This new version of CyTag was developed by Bethan Tovey-Walsh <bytheway@linguacelta.com>, 2018-2021. It reuses some elements of the original CyTag, with a new object-oriented architecture for the tagger and bilingual user interface.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

import sys
import os
from pathlib import Path
from termcolor import colored
import click
import time
import argparse


# Set trace to "True" if you want the constraint grammar module to print an extra output file showing which rules were used to decide on final pos tags.

trace = False

def set_language():
    language = click.prompt("Type [E] to run CorCenCC with an English-language interface...\nTeipiwch [C] i ddefnyddio CorCenCC gyda rhyngwyneb cyfrwng Cymraeg...\n")
    while language.lower() not in ["c", "e"]:
        language = click.prompt("Please press either the letter [E] or the letter [C] on your keyboard to set the interface language, then hit Enter.\nPwyswch y naill ai'r allwedd [C] neu'r allwedd [E] ar eich bysellfwrdd i ddewis iaith y rhyngwyneb, a wedyn bwrwch Enter.")
    return language

def ask_user(language, lex_refresh):
    if language == "c":
        output_name = click.prompt("\n\nTeipiwch enw i'r ffolder allbwn")
        if lex_refresh != "done":
            lexica = click.prompt("Hoffech (ail-)adeiladu'r lecsica? ([I]e/[N]a, neu [H] am fwy o wybodaeth).")
            if lexica.lower() in ["i", "ie"]:
               lexica_refresh(language)
            elif lexica.lower() == "h":
                lexica = click.prompt("\nAil-adeiladwch y lecsica y tro cyntaf i chi rhedeg y cod.\nDylsech ail-adeiladu hefyd os fu newidiadau i'r geiriaduron ers y tro diwethaf i chi rhedeg y cod..\n\n(Os nad ydych yn sicr, dewiswch [I] i ail-adeiladu - does dim i'w golli ond amser!)\n\nTeipiwch [I] i ail-adeiladu, neu [N] i rhedeg y cod heb ail-adeiladu.")
        else:
            lexica = "n"
        unknown_reset = click.prompt("Hoffech ailosod y rhestr geiriau anhysbus? ([I]e/[N]a, neu [H] am fwy o wybodaeth).")
        if unknown_reset.lower() in ["i", "ie"]:
            unknown_reset = "yes"
        elif unknown_reset.lower() in ["h", "help"]:
            unknown_reset = click.prompt("\nOs nad ail-osodwch y rhestr, fydd y rhestr yn cynnwys geiriau anhysbus canfyddwyd gan CorCenCC yn y gorffennol.\n\nOs ail-osodwch, fe fydd y rhestr yn dechrau'n wag, a dim ond geiriau darganfyddwch o hyn ymlaen cewch weld yn y rhestr.\n\nTeipiwch [I] i ail-ddechrau gyda rhestr wag, neu [N] i gadw'r hen rhestr ac ychwanegu geiriau newydd iddo.")
        elif unknown_reset.lower() not in ["i", "ie", "n", "na", "h", "help"]:
            unknown_reset = click.prompt("\nSori, dwi ddim yn deall! Teipiwch [I] (ie) neu [N] (na), neu teipiwch [H] i gael help gyda'ch dewis.")
    else:
        output_name = click.prompt("\n\nPlease type a name for the output directory")
        if lex_refresh != "done":
            lexica = click.prompt("Do you want to (re)build the lexica? (Type [Y]/[N], or [H] for more information)")
            if lexica.lower() in ["y", "yes"]:
                lexica_refresh(language)
            if lexica.lower() == "h":
                lexica = click.prompt("\nRebuilding the lexica should be done when you first run this code.\nYou should also rebuild if you've made any changes to the dictionary files since the last time you ran this code.\n\n(If you're unsure whether the rebuild is needed, choose [Y]. Better safe than sorry!)\n\nType [Y] to rebuild, or [N] to run the code without rebuilding.")
        else:
            lexica = "n"
        unknown_reset = click.prompt("Do you want to reset the list of unknown words? (Type [Y]/[N], or [H] for more information)")
        if unknown_reset.lower() in ["y", "yes"]:
            unknown_reset = "yes"
        if unknown_reset.lower() in ["h", "help"]:
            unknown_reset = click.prompt("\nReset the list if you want to start with a blank slate. If you do not reset, previously unknown words will be retained, and new words added to the end of the list.\n\n(If you're unsure whether the reset is needed, choose [N] so that you don't lose your previously-acquired data.)\n\nType [Y] to restart with a blank list, or [N] to add to the list without resetting.")
        if unknown_reset.lower() not in ["y", "yes", "n", "no", "h", "help"]:
            unknown_reset = click.prompt("\nI'm sorry, I don't understand. Please type [Y] (yes) to reset the list of unknown words; [N] (no) to continue by adding to the existing list; or [H] for more information.")

    return(output_name, lexica, unknown_reset)

def setup_outputs(output_name, unknown_reset, language, prefix=None):
    """ Create the output directory and set up the required output files. Note that the default directory names are language-dependent."""
    if language == "c":
        base_dir = "allbwn"
    elif language == "e":
        base_dir = "output"
    out = Path(base_dir)
    out.mkdir(exist_ok=True)
    dir_name = base_dir + "/" + output_name    
    output_dir = Path(dir_name)
    output_dir.mkdir(exist_ok=True)
    map_file = Path(output_dir/"map.tsv")
    map_file.touch()
    filenames = {}
    if language == "c":
        filenames["rfile"] = "darlleniadau"
        filenames["rcgfile"] = "darlleniadauWediCG"
        filenames["tracefile"] = "darlleniadauWediCG_TRACE"
        filenames["tsvfile"] = "canlyniad"
        filenames["unkfile"] = "geiriau_anhysbus"
        for item in filenames:
            if prefix != None:
                filenames[item] = "{}_{}.txt".format(filenames[item],prefix)
            else:
                filenames[item] = filenames[item] + ".txt"
        filenames["tsvfile"] = filenames["tsvfile"][:-4] + ".tsv"
    elif language == "e":
        filenames["rfile"] = "readings"
        filenames["rcgfile"] = "readingsPostCG"
        filenames["tracefile"] = "readingsPostCG_TRACE"
        filenames["tsvfile"] = "result"
        filenames["unkfile"] = "unknown_words"
        for item in filenames:
            if prefix != None:
                filenames[item] = "{}_{}.txt".format(filenames[item],prefix)
            else:
                filenames[item] = filenames[item] + ".txt"
        filenames["tsvfile"] = filenames["tsvfile"][:-4] + ".tsv"
    with open (map_file, 'w') as mfile:
        mfile.write("")
    readings_file = Path(output_dir/filenames["rfile"])
    readings_file.touch()
    with open (readings_file, 'w') as rfile:
        rfile.write("")
    readings_post_cg_file = Path(output_dir/filenames["rcgfile"])
    readings_post_cg_file.touch()
    with open (readings_post_cg_file, 'w') as rpcgfile:
        rpcgfile.write("")
    readings_post_cg_tracefile = None
    if trace == True:
        readings_post_cg_tracefile = Path(output_dir/filenames["tracefile"])
        readings_post_cg_tracefile.touch()
        with open (readings_post_cg_tracefile, 'w') as rpcgtfile:
            rpcgtfile.write("")
    tsv_file = Path(output_dir/filenames["tsvfile"])
    tsv_file.touch()
    with open (tsv_file, 'w') as tsvfile:
        tsvfile.write("")
    unknown_file = Path(output_dir/filenames["unkfile"])
    unknown_file.touch()
    if unknown_reset in ["yes", "y", "ie", "i"]:
        with open (unknown_file, 'w') as unkfile:
            unkfile.write("")
    return(readings_file, readings_post_cg_file, readings_post_cg_tracefile, tsv_file, unknown_file, map_file)

def lexica_refresh(language, no_gaz=False):
    from postagger.reference_lists.load_lexica import load_lexica
    load_lexica(language, no_gaz)

def run_tagger(text, file_id, readings_file, readings_post_cg_file, readings_post_cg_tracefile, tsv_file, unknown_file, file_name, filetotal, para_count, para_index):
    if language == "c":
        msg = "Tagio {}".format(file_name[:-4])
    else: 
        msg = "Tagging {}".format(file_name[:-4])
    sent_index = 1
    for para in text.paragraphs():
        if filetotal > 10:
            curr_pc = int("{:.0f}".format((para_index/para_count)*100))
            sys.stdout.flush()
            sys.stdout.write("\r{} [{}% o'r cyfanswm]\r".format(msg, curr_pc))
            para_index += 1
        else:
            print(msg, end='\r')
        cg_in_sents = ""
        unknown_list = set()
        for sent in para.sentences():
            unknowns = sent.unknowns()
            for unk in unknowns:
                unknown_list.add(unk)
            cg_in = sent.cg_input(sent_index)
            cg_in_sents += cg_in
            cg_in_sents += "\n"
            sent_index += 1
            with open(readings_file, 'a') as r_outfile:
                r_outfile.write(cg_in)
        cg_out = para.cg_output(cg_in_sents)
        with open(readings_post_cg_file, 'a') as cg_outfile:
             cg_outfile.write(cg_out)
        if trace == True:
            with open(readings_post_cg_tracefile, 'a') as cg_tracefile:
                cg_tracefile.write(para.cg_output_trace(cg_in_sents))
        with open(tsv_file, 'a') as tsv_outfile:
            tsv_outfile.write(para.tsv_output(cg_out, file_id))
        unknown_list = sorted(unknown_list)
        with open(unknown_file, 'a') as unk_file:
            unk_items = ""
            for unk_item in unknown_list:
                unk_items += unk_item
                unk_items += "\n"
            unk_file.write(unk_items)
    return para_index


if __name__ == "__main__":
    start_time = time.perf_counter()
    parser = argparse.ArgumentParser(description="CyTag: tagiwr rhan ymadrodd i'r Gymraeg.\nCyTag: a Welsh part-of-speech tagger.")
    # The -c flag allows the user to bypass the prompts for information such as output filenames. 
    # DEFAULTS: 
    # "cytag" for the output filename, 
    # Welsh for the language of messages and output directories
    # reset the list of unknown words before running the code
    # These defaults can be changed below.
    parser.add_argument("-c", "--cyf", action='store_const', const=1, help="Rhedeg gyda'r rhagosodiadau. / Run with default values.")
    # The lexica should be rebuilt every time the main lexicon files are changed. Until this is done, the code will continue to use cached versions of the lexicon files.
    parser.add_argument("-l", "--lex", action='store_const', const=1, help="Ail-adeiladu'r lecsica Cymraeg a Saesneg. / Rebuild the Welsh and English lexica.")
    parser.add_argument("-p", "--pre", action='store_const', const=1, help="Cyn-brosesu data CorCenCC. / Pre-process CorCenCC data.")
    parser.add_argument("-b", "--blaen", help="Gosod blaenddod i ddewis is-set o ffeiliau mewnbwn. / Set a prefix to select a subset of input files.")
    args = parser.parse_args()
    prefix = None
    lex_refresh = None
    if args.cyf == 1:
        # To change defaults:
        # set language to "e" for English messages and  directory/file names
        # set unknown_reset to "n" to keep previous list of unknown words and add new unknowns to the end of the list
        # change output_name to a different string to change the default output filename
        language = "c"
        output_name = "cytag"
        unknown_reset = "i"
    else:
        language = set_language().lower()
    if args.lex == 1:
        # This flag allows the user to refresh the lexica without refreshing the gazetteers. The gazetters are slow to refresh, so this option is the best one if only the Welsh or English lexicon file has been changed.
        lexica_refresh(language, no_gaz=True)
        lex_refresh = "done"
    if args.cyf != 1:
        if language == "c":
            prefs = "\n\n## GOSODWCH EICH DEWISIADAU ##\n\n"
        else:
            prefs = "\n\n## SET PREFERENCES ##\n\n"
        prefs_message = colored(prefs, attrs=['reverse', 'bold'])
        print(prefs_message) 
        output_name, lexica, unknown_reset = ask_user(language, lex_refresh)

    if args.blaen != None:
        globnames = args.blaen + "*.txt"
        input_files = sorted(Path("inputs/cleaned").glob(globnames))
    else:
        # By default, CorCenCC expects input in the form of one or more .txt files, placed in the "txt" subdirectory.
        input_files = sorted(Path("txt").glob("*.txt"))

    if args.pre == 1:
        preprocess_corcencc = "y"
    else:
        preprocess_corcencc = "n"
    
    if args.blaen != None:
        # This option was used to tag the the CorCenCC subcorpora.
        output_name = args.blaen
        prefix = args.blaen

    if language == "c":
        directories = "\nWrthi'n creu cyfeiriaduron allbwn...\n"
    else:
        directories = "\nCreating output folders...\n"
    print(directories)
    readings_file, readings_post_cg_file, readings_post_cg_tracefile, tsv_file, unknown_file, map_file = setup_outputs(output_name, unknown_reset, language, prefix)

    if language == "c":
        startup = "\n\n## WRTHI'N DECHRAU'R TAGIWR ##\n\n"
    else:
        startup = "\n\n## INITIALIZING THE TAGGER ##\n\n"
    startup_message = colored(startup, attrs=['reverse', 'bold'])
    print(startup_message)

    # imports happen here so that they take account of reloaded lexica when applicable #

    import postagger.tokenizer as tokenizer
    import postagger.preprocessor as preprocessor
    
    para_count = 0
    if language == "c":
        print(f"\n\nCasglu mewnbynnau...\n\n")
    else: 
        print(f"\n\nCollecting input files...\n\n")

    filetotal = len(input_files)
    for file in input_files:
        with open (file, 'r') as infile:
            rawtext = infile.read()
            text = tokenizer.Text(rawtext, infile.name, "000")
            para_count += len(text.paragraphs())
    if language == "c":
        print(f"{para_count} paragraff i dagio, o fewn {filetotal} ffeil...\n\n")
    else: 
        print(f"{para_count} paragraph(s) to tag in {filetotal} files...\n\n")
    
    pc = 0

    if language == "c":
        print(f"Mae CyTag nawr yn tagio'ch ffeliau mewnbwn...\n\n")
    else: 
        print(f"CyTag is tagging your input files...\n\n")

    para_index = 1
    for i, file in enumerate(input_files):
        if language == "c":
            print(f"Ffeil {str(i+1)} o {filetotal} ffeil...\n\n")
        else: 
            print(f"File {str(i+1)} of {filetotal} files...\n\n")
        file_name = os.path.basename(str(file))
        file_id = str(i+1)
        while len(file_id) < 6:
            file_id = "0" + file_id
        with open (map_file, 'a') as mfile:
            mfile.write("{}\t{}\n".format(file_name, file_id))
        with open (file, 'r') as infile:
            rawtext = infile.read()                
            text = tokenizer.Text(rawtext, file_name, file_id, preproc=preprocess_corcencc)
            para_index = run_tagger(text, file_id, readings_file, readings_post_cg_file, readings_post_cg_tracefile, tsv_file, unknown_file, file_name, filetotal, para_count, para_index)


