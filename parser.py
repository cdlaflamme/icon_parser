# parser.py
import pymupdf
import re
from enum import Enum

"""
have heirarchy structure and node classes created
need to loop through content and start matching patterns
problems:
- remove page lines
- need to figure out how to identify every kind of line (rules vs flavor, mostly)
-- this is just based on whatever the previous type was
"""

def main():
    data = parse_data()
    for line_data in data:
        print(line_data)
    
def parse_data():
    DATA_PATH = "icon2.pdf"
    
    #inclusive ranges of PRINTED PAGES for each class/color
    page_ranges = [
        slice( 37-1, 64-1+1), #stalwart
        slice( 67-1, 94-1+1), #vagabond
        slice( 97-1,124-1+1), #mendicant
        slice(127-1,154-1+1), #wright
    ]
    
    lines = []

    # extract and format lines
    with pymupdf.open(DATA_PATH) as doc:
        for s in page_ranges:
            for page in doc[s]:
                d = page.get_text("dict", sort=False)
                for block in d['blocks']:
                    for line in block['lines']:
                        
                        x = line['spans'][0]['bbox'][0]
                        y = line['spans'][0]['bbox'][1]
                        
                        if y > 730: continue #skip page number lines
                        
                        text = ''
                        for span in line['spans']:
                            text = text + span['text']
                        lines.append((x, text))
    
    line_contexts = []       
    context_type = None
    last_type = None
    last_indented = False
    
    for x,line in lines:

        type = None
    
        # decide if line is indented
        indented = False
        if 100 < x < 110 or 330 < x < 355:
            indented = True
        
        if not indented:
            if (is_line_soul(line)):
                type = LineType.SOUL
                context_type = type
            elif (is_line_job(line)):
                type = LineType.JOB
                context_type = type
            elif (is_line_ability(line)):
                type = LineType.ABILITY
                context_type = LineType.ABILITY
            elif is_line_keyword(line):
                type = LineType.KEYWORD
                context_type = LineType.KEYWORD
            elif is_line_lb(line):
                type = LineType.GLUE
                context_type = LineType.LB
            elif is_line_talents(line):
                type = LineType.GLUE
                context_type = LineType.TALENT
        
        if type is None:
            if context_type == LineType.SOUL:
                type = LineType.FLAVOR
            elif context_type == LineType.JOB:
                if is_line_all_caps(line):
                    type = LineType.TRAIT
                    context_type = type
                else:
                    type = LineType.FLAVOR
            elif context_type == LineType.TRAIT:
                type = LineType.TRAIT_RULES
            elif context_type == LineType.KEYWORD:
                if is_line_glue(line):
                    type = LineType.GLUE
                else:
                    type = LineType.KW_RULES
            elif context_type == LineType.TALENT:
                if is_line_all_caps(line):
                    type = LineType.TALENT
                else:
                    type = LineType.TALENT_RULES
            elif context_type == LineType.ABILITY or LineType.AB_PART or LineType.LB:
                if is_line_all_caps(line):
                    type = LineType.LB
                elif last_type == LineType.LB:
                    type = LineType.LB_INFO1
                elif last_type == LineType.LB_INFO1:
                    type = LineType.LB_INFO2 # TODO not every Lb has two lines; use italics or keywords to tell
                elif last_type == LineType.ABILITY:
                    type = LineType.AB_INFO
                elif is_line_ab_part(line) and not indented:
                    type = LineType.AB_PART
                    context_type = LineType.AB_PART
                else:
                    if context_type == LineType.ABILITY or context_type == LineType.LB:
                        type = LineType.FLAVOR
                    elif context_type == LineType.AB_PART:
                        if indented:
                            if not last_indented:
                                type = LineType.SUB_ABILITY
                            elif last_type == LineType.SUB_ABILITY:
                                type = LineType.SAB_INFO
                            elif is_line_ab_part(line):
                                type = LineType.SAB_PART
                            else:
                                type = LineType.SAB_RULES
                        elif is_line_glue(line):
                            type = LineType.GLUE
                        else:
                            type = LineType.AB_RULES
        if type == LineType.AB_RULES or type == LineType.SAB_RULES:
            if is_line_reminder(line) or last_type == LineType.REMINDER:
                type = LineType.REMINDER
        
        last_type = type
        last_indented = indented
        line_context = (context_type, type, line)
        line_contexts.append(line_context)
    return line_contexts

class LineType(Enum):
    SOUL        = 1
    JOB         = 2
    KEYWORD     = 3
    KW_RULES    = 305
    LB          = 4
    LB_INFO1    = 401
    LB_INFO2    = 402
    LB_RULES    = 405    
    TALENT      = 5
    TALENT_RULES= 505
    FLAVOR      = 6
    TRAIT       = 7
    TRAIT_RULES = 705
    ABILITY     = 8
    AB_PART     = 802
    AB_INFO     = 801
    AB_RULES    = 805
    SUB_ABILITY = 9
    SAB_INFO    = 901
    SAB_PART    = 902
    SAB_RULES   = 905
    GLUE        = 999
    REMINDER    = 1000    

def is_line_soul(line):
    m = re.match('\\w+ SOUL', line)
    return m is not None

def is_line_job(line):
    m = re.match('\\d+\\. [A-Z]+', line)
    return m is not None
    
def is_line_all_caps(line):
    m = re.match('^[A-Z\\W]+$', line)
    return m is not None
    
def is_line_ability(line):
    m = re.match('[IV]+\\. [A-Z\\W]+', line)
    return m is not None

def is_line_keyword(line):
    m = re.match('keyword\\W*', line.lower())
    return m is not None

def is_line_lb(line):
    m = re.match('limit break:\W*$', line.lower())
    return m is not None

def is_line_talents(line):
    m = re.match('talents:\W*$', line.lower())
    return m is not None

def is_line_reminder(line):
    m = re.match('\\(.*\\:.*', line)
    return m is not None

def is_line_glue(line):
    lower_line = line.lower()
    m = re.match('abilities\W*', lower_line)
    if m: return True
    
    m = re.match('master:{0,1} *$', lower_line)
    if m: return True
    
    return False

#ignore [x] in these phrases; those are checked for separately
ab_part_phrases = [
    'attack',
    'on hit',
    'effect',
    'summon',
    'area effect',
    'zone',
    'trigger',
    'stance',
    'overdrive',
    'impact',
    'heavy',
    'conserve',
    'excel',
    'critical hit',
    'reckless',
    'sacrifice',
    'dominant',
    'afflicted',
    'mark',
    'finishing blow',
    'isolate',
    'precision',
    'gambit',
    'weave',
    'aura',
    'summon action',
    'summon effect',
]

def is_line_ab_part(line):
    #find colon; fetch text until colon; this is the "key"
    m = re.match('([\\w\\W]+?) {0,1}[d\\d]*(?:\\[x\\]){0,1}: .+', line.lower())
    if m is None: return False
    
    #match key to list of approved phrases
    key = m[1]
    #if any match, we have an ability part
    if (key in ab_part_phrases):
        return True
    # if the key is not in there exactly, try the first word (for cases like "sacrifice 3 or gain reckless:")
    else:
        return (key.strip().split(' ')[0] in ab_part_phrases)

if __name__ == "__main__":
	main()