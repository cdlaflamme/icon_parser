# parser.py
import pymupdf
import odfdo as odf

import re
from enum import Enum

def main():
    data = get_data()
    for line_data in data:
        print(line_data)

def get_data():
    DATA_PATH = "icon2.pdf"
    line_info = get_lines(DATA_PATH) 
    block_info = get_blocks(line_info)
    return block_info

def get_blocks(data):
    
    blocks = []
    currentBlock = None
    currentSoul = None
    # Combine lines into blocks of contiguous type organized in a tree heirarchy
    for line_info in data:
        # Organize line info
        line_context_type, line_type, line_text = line_info
        
        # Analyze line
        # If we should start a new block
        if currentBlock is None or currentBlock.type != line_type:
            oldBlock = None
            # If we were working on a block before this:
            if currentBlock is not None:
                # Wrap up old block
                oldBlock = currentBlock
                # Clean up text a bit
                oldBlock.finalizeText()

            # Determine desired parent type
            desired_p_type = Block.parent_type_dict[line_type]
            found_parent = None
            
            # Find parent for new block in heirarchy
            # If a parent is desired at all and we have previous blocks to work on:
            if desired_p_type != 0 and oldBlock is not None:
                # If any parent is acceptable, use previous block
                if desired_p_type == 1:
                    found_parent = oldBlock                
                elif oldBlock.type == desired_p_type: found_parent = oldBlock
                else: found_parent = oldBlock.getAncestorOfType(desired_p_type)
            
            # Create new block and add to tree
            currentBlock = Block(line_type, soul=currentSoul)
            if found_parent is not None:
                currentBlock.setParent(found_parent)
            else:
                blocks.append(currentBlock)
                assert line_type == LineType.SOUL # :)
                currentSoul = re.match('([A-Z]+)\\W+SOUL',line_text)[1]
                currentBlock.soul = currentSoul
        
        # For either new blocks or continuing blocks:
        # Add text to current block
        currentBlock.addText(line_text)
    return blocks
    
def get_lines(in_path):
    
    #inclusive ranges of PRINTED PAGES for each class/color
    page_ranges = [
        slice( 37-1, 64-1+1), #stalwart
        slice( 67-1, 94-1+1), #vagabond
        slice( 97-1,124-1+1), #mendicant
        slice(127-1,154-1+1), #wright
    ]
    
    lines = []

    # extract and format lines
    with pymupdf.open(in_path) as doc:
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
                            
                        if text.strip() == '': continue # skip empty lines
                        
                        lines.append((x, text))
    
    line_contexts = []       
    context_type = None
    last_type = None
    last_indented = False
    in_bullets = False
    for x,line in lines:

        type = None
    
        # decide if line is indented
        indented = False
        if 107 < x < 127 or 330 < x < 365:
            indented = True
        
        # decide if this line is bulleted
        bulleted = is_line_bulleted(line)
        
        # decide if this line looks like an info line
        is_info = is_line_info(line)
        
        if not indented:
            if (is_line_soul(line)):
                type = LineType.SOUL
                context_type = type
            elif (is_line_job(line)):
                type = LineType.JOB
                context_type = type
            elif is_line_abilities_header(line):
                type = LineType.GLUE
                context_type = LineType.ABILITY
            elif (is_line_ability(line)):
                type = LineType.ABILITY
                context_type = LineType.ABILITY
            elif is_line_keyword(line):
                type = LineType.KEYWORD
                context_type = LineType.KEYWORD
            elif is_line_trait(line):
                type = LineType.GLUE
                context_type = LineType.TRAIT
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
                # Check for an unlebelled trait. necessary because of tactician (at least)
                if is_line_all_caps(line):
                    type = LineType.TRAIT
                    context_type = type
                else:
                    type = LineType.FLAVOR
            elif context_type == LineType.TRAIT:
                if last_type == LineType.GLUE:
                    type = LineType.TRAIT
                elif indented and not last_indented:
                    type = LineType.SUB_TRAIT
                    context_type = type
                else:
                    type = LineType.TRAIT_RULES
            elif context_type == LineType.SUB_TRAIT and indented:
                if is_line_info(line):
                    type = LineType.ST_INFO
                elif is_line_ab_part(line):
                    type = LineType.ST_PART
                else:
                    type = LineType.ST_RULES
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
            elif context_type in [LineType.ABILITY, LineType.AB_PART, LineType.LB_PART, LineType.LB, LineType.SUB_ABILITY, LineType.SUB_LB]:
                is_lb_context = context_type in [LineType.LB_PART, LineType.LB, LineType.SUB_LB]
                if is_line_all_caps(line) and last_type in [LineType.GLUE, LineType.LB] and context_type == LineType.LB:
                    type = LineType.LB
                elif last_type == LineType.LB and is_info:
                    type = LineType.LB_INFO1
                elif last_type == LineType.LB_INFO1 and is_info:
                    type = LineType.LB_INFO2
                elif last_type == LineType.ABILITY and is_info:
                    type = LineType.AB_INFO
                elif is_line_ab_part(line) and not indented:
                    type = LineType.LB_PART if is_lb_context else LineType.AB_PART
                    context_type = type
                else:
                    if context_type in [LineType.ABILITY, LineType.LB]:
                        type = LineType.FLAVOR
                    elif context_type in [LineType.AB_PART, LineType.LB_PART, LineType.SUB_ABILITY, LineType.SUB_LB]:
                        if indented and (context_type in [LineType.SUB_ABILITY, LineType.SUB_LB]) or (indented and not (bulleted or in_bullets)):
                            if not last_indented:
                                type = LineType.SUB_LB if is_lb_context else LineType.SUB_ABILITY
                                if not (is_line_reminder(line)): context_type = type
                            elif last_type in [LineType.SUB_ABILITY, LineType.SUB_LB] and is_info:
                                type = LineType.SLB_INFO if is_lb_context else LineType.SAB_INFO
                            elif is_line_ab_part(line):
                                type = LineType.SLB_PART if is_lb_context else LineType.SAB_PART
                            else:
                                type = LineType.SLB_RULES if is_lb_context else LineType.SAB_RULES
                        elif is_line_glue(line):
                            type = LineType.GLUE
                        else:
                            type = LineType.LB_RULES if is_lb_context else LineType.AB_RULES
                            
        if type in [LineType.AB_RULES, LineType.LB_RULES, LineType.SAB_RULES, LineType.SLB_RULES, LineType.SUB_ABILITY, LineType.SUB_LB]:
            if is_line_reminder(line) or last_type == LineType.REMINDER:
                type = LineType.REMINDER
        
        last_type = type
        last_indented = indented
        in_bullets = bulleted or (in_bullets and indented)
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
    LB_INFO2    = 4012
    LB_PART     = 402
    LB_RULES    = 405
    SUB_LB      = 410
    SLB_INFO    = 411
    SLB_PART    = 412
    SLB_RULES   = 415
    TALENT      = 5
    TALENT_RULES= 505
    FLAVOR      = 6
    TRAIT       = 7
    TRAIT_RULES = 705
    SUB_TRAIT   = 710
    ST_INFO     = 711
    ST_PART     = 712
    ST_RULES    = 715
    ABILITY     = 8
    AB_INFO     = 801
    AB_PART     = 802
    AB_RULES    = 805
    SUB_ABILITY = 810
    SAB_INFO    = 811
    SAB_PART    = 812
    SAB_RULES   = 815
    GLUE        = 999
    REMINDER    = 1000    

class Block:
    def __init__(self, type, text = '', style = '', soul = '', job_class = ''):
        self.parent = None
        self.children = []
        self.type = type
        self.text = text
        self.style = style
        self.soul = soul
        self.job_class = job_class
    
    def addChild(self, child):
        self.children.append(child)
        child.setParent(self)
    
    def setParent(self, parent):
        self.parent = parent
        if self not in parent.children:
            parent.addChild(self)
        
    def addText(self, text):
        self.text = self.text + text
    
    def finalizeText(self):
        # trim newlines at the end
        #self.text = re.sub('\\n$', '', self.text)
        self.text = self.text.strip()
    
    # Searches up the chain for an ancestor of supplied type
    def getAncestorOfType(self, type):
        b = self.parent
        while b is not None and b.type != type:
            b = b.parent
        return b # Might be None
    
    # Searches down the tree, depth first, for the first descendant of the supplied type
    def getDescendantOfType(self, type):
        # Base case: no children
        if self.children == []:
            return None
        
        for child in self.children:
            if child.type == type:
                return child
            else:
                found = child.getDescendantOfType(type)
                if found is not None:
                    return found
        
        # If nobody was found:
        return None
    
    
    # Searches down the tree for all descendants of the supplied type
    def getAllDescendantsOfType(self, type):
        # Base case: no children
        if self.children == []:
            return []
        
        # Get children, recursively
        found = []
        for child in self.children:
            if child.type == type: found.append(child)
            found = found + child.getAllDescendantsOfType(type)
        
        return [c for c in found if c.type == type]
    
    
    # For each block type, what kind of block should it look for in a parent
    # Special values:
    # 0: no parent
    # 1: any parent
    parent_type_dict = {
        LineType.SOUL        : 0,
        LineType.JOB         : LineType.SOUL,
        LineType.KEYWORD     : LineType.JOB,
        LineType.KW_RULES    : LineType.KEYWORD,
        LineType.LB          : LineType.JOB,
        LineType.LB_INFO1    : LineType.LB,
        LineType.LB_INFO2    : LineType.LB,
        LineType.LB_PART     : LineType.LB,
        LineType.LB_RULES    : LineType.LB_PART,
        LineType.SUB_LB      : LineType.LB_PART,
        LineType.SLB_INFO    : LineType.SUB_LB,
        LineType.SLB_PART    : LineType.SUB_LB,
        LineType.SLB_RULES   : LineType.SLB_PART,
        LineType.TALENT      : LineType.JOB,
        LineType.TALENT_RULES: LineType.TALENT,
        LineType.FLAVOR      : 1,
        LineType.TRAIT       : LineType.JOB,
        LineType.TRAIT_RULES : LineType.TRAIT,
        LineType.SUB_TRAIT   : LineType.TRAIT,
        LineType.ST_INFO     : LineType.SUB_TRAIT,
        LineType.ST_PART     : LineType.SUB_TRAIT,
        LineType.ST_RULES    : LineType.ST_PART,
        LineType.ABILITY     : LineType.JOB,
        LineType.AB_INFO     : LineType.ABILITY,
        LineType.AB_PART     : LineType.ABILITY,
        LineType.AB_RULES    : LineType.AB_PART,
        LineType.SUB_ABILITY : LineType.AB_PART,
        LineType.SAB_INFO    : LineType.SUB_ABILITY,
        LineType.SAB_PART    : LineType.SUB_ABILITY,
        LineType.SAB_RULES   : LineType.SAB_PART,
        LineType.GLUE        : 1,
        LineType.REMINDER    : 1,
    }
    
    def __repr__(self):
        return 'Block(type=%s, text=\'%s\', style=\'%s\', soul=\'%s\', job_class=\'%s\')' % (self.type, self.text, self.style, self.soul, self.job_class)

def is_line_soul(line):
    m = re.match('^\\W*[a-zA-Z]+ SOUL\\W*$', line)
    return m is not None

def is_line_job(line):
    m = re.match('\\d+\\. [A-Z ]+$', line)
    return m is not None
    
def is_line_all_caps(line):
    m = re.match('^[A-Z ]+$', line.strip())
    return m is not None

def is_line_abilities_header(line):
    m = re.match('abilities:{0,1}$', line.lower().strip())
    return m is not None

def is_line_ability(line):
    # Add hacks for Ätherwand and war god's step
    m = re.match('[IV]+\\. [ÄA-Z\\W]+', line)
    if m: return True
    
    m = re.match('WAR GOD\'S STEP', line)
    if m: return True
    
    return False


def is_line_keyword(line):
    m = re.match('keyword\\W*', line.lower())
    return m is not None

def is_line_trait(line):
    m = re.match('trait:{0,1}$', line.lower().strip())
    return m is not None

def is_line_lb(line):
    m = re.match('limit break:{0,1}\W*$', line.lower())
    return m is not None

def is_line_talents(line):
    m = re.match('talents:{0,1}\W*$', line.lower())
    return m is not None

def is_line_reminder(line):
    m = re.match('\\(.*\\:.*', line)
    return m is not None

def is_line_glue(line):
    lower_line = line.lower()
    m = re.match('abilities\W*$', lower_line)
    if m: return True
    
    m = re.match('master:{0,1} *$', lower_line)
    if m: return True
    
    return False

def is_line_bulleted(line):
    lower_line = line.lower().strip()
    
    m = re.match('\\d+\\..*', lower_line)
    if m: return True
    
    m = re.match('•.*', lower_line)
    if m: return True
    
    # technially not bulleted but logically equivalent; used in curtain call
    # using a not-general hack because anything general breaks too much and isn't worth it
    m = re.match('[0346\\- spaces6\\+]+:', lower_line)
    if m: return True
    """
    m = re.match('^[\\w\\-\\W]+:', lower_line)
    # otherwise causes all sub aility parts to be designated as bulleted
    if m and not is_line_ab_part(line): return True
    """
    
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
    m = re.match('([\\w\\W]+?) {0,1}[d\\d]*(?:\\[x\\]){0,1}[:\\.] .+', line.lower())
    if m is None: return False
    
    #match key to list of approved phrases
    key = m[1]
    #if any match, we have an ability part
    if (key in ab_part_phrases):
        return True
    # if the key is not in there exactly, try the first word (for cases like "sacrifice 3 or gain reckless:")
    else:
        return (key.strip().split(' ')[0] in ab_part_phrases)

info_phrases = [
    'interrupt',
    'attack',
    'zone',
    'aura',
    'push',
    'stance',
    'mark',
    'summon',
    'swap',
    'object',
    
    'range',
    'melee',
    'close',
    'adjacent',
    
    'action',
    'actions',
    'quick',
    
    'ally',
    'foe',
    'self',
    
    'end',
    'turn',
    
    'blast',
    'burst',
    'arc',
    'line',
    'cross',
    
    'resolve',
    'x',
    'power',
    'die',
    'immobile',
    'size',
    'height',
    
    'true',
    'strike'
]

def is_line_info(line):
    words_only = re.sub('[^a-z]', ' ', line.lower().strip())
    single_spaced = re.sub(' +', ' ', words_only.strip())
    words = single_spaced.split(' ')
    
    if len(words) == 0: return False
    for word in words:
        if word not in info_phrases: return False
    
    return True

if __name__ == "__main__":
	main()