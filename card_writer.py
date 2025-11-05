# card_writer.py
from enum import Enum
import re

import odfdo as odf

import parser as parser
from parser import LineType

import doc_utils as doc_utils


def main():
    
    blocks = parser.get_data()
        
    # Process blocks and write to document
    doc = doc_utils.open_icon_doc()
    body = doc.body
    body.clear()
    
    talent_doc = odf.Document('odt')
    t_body = talent_doc.body
    t_body.clear()
    doc_utils.get_talent_styles(talent_doc)
    
    # TODO make better use of this; created halfway thru implementation
    writer = BlockWriter(body)
    
    # every parent block is (nominally) a soul!
    for soul in blocks:
        
        # get each job within
        jobs = soul.getAllDescendantsOfType(LineType.JOB)
        
        for job in jobs:
            # card 1: job name, keyword, trait, limit break
            # - consider flavor on the back...
            
            # Job Name
            j_class = Styler.get_job_class_for_soul(job.soul).value
            j_name = re.match('\\d+\\. ([A-Z ]+)', job.text)[1] # used later
            p = odf.Paragraph(job.text, style = j_class + ' Job')
            body.append(p)
            
            # Soul
            p = odf.Paragraph(soul.text.title())
            p.set_span('Italics', regex = '.*')
            body.append(p)
                
            # Keyword
            kw = job.getDescendantOfType(LineType.KEYWORD)
            kw_text = kw.children[0].text
            kw_m = re.match('([ \\w]+):', kw_text)
            if kw_m:
                kw_name = kw_m[1]
            
            body.append(odf.Paragraph('Keyword', style='Simple Header'))
            p = odf.Paragraph(kw_text)
            if kw_m: p.set_span('Bold', regex = '^'+kw_name)
            body.append(p)
            
            # Trait
            t = job.getDescendantOfType(LineType.TRAIT)
            t_name = t.text.title()
            t_rules = t.children[0].text
            body.append(odf.Paragraph('Trait', style='Simple Header'))
            p = odf.Paragraph(t_name.title() + ': ' + t_rules)
            p.set_span('Bold', regex = '^'+t_name)
            body.append(p)
            
            sub_item = t.getDescendantOfType(LineType.SUB_TRAIT)
            
            if sub_item:
                # Print sub item name and info
                # Name
                body.append(odf.Paragraph(sub_item.text.title(), style = j_class + ' Sub-item'))
                
                # Info line(s)
                info = sub_item.getDescendantOfType(LineType.ST_INFO)
                body.append(odf.Paragraph(info.text.strip().title(), style = 'Sub-item'))
                
                # Print sub parts
                sub_parts = sub_item.getAllDescendantsOfType(LineType.ST_PART)
                for sub_part in sub_parts:
                    text = sub_part.text
                    sub_rules   = sub_part.getAllDescendantsOfType(LineType.ST_RULES)
                    if sub_rules:
                        for rule in sub_rules:
                            text = text + ' ' + rule.text
                    p = odf.Paragraph(Styler.fix_spaces(text.strip()), style = 'Sub-item')
                    
                    # Identify part key
                    m = re.match(BlockWriter.ab_part_key_regex, sub_part.text.lower())
                    key = m[1]
                    
                    # Bold ability part key
                    p.set_span('Bold Sub-item', regex = '(?i)^'+key)
                    body.append(p)
                        
            # Limit Break
            lb = job.getDescendantOfType(LineType.LB)
            # Title
            body.append(odf.Paragraph('\nLimit Break', style = 'New Column Header'))
            body.append(odf.Paragraph(lb.text.upper(), style = j_class))
            
            # Info line(s)
            info1 = job.getDescendantOfType(LineType.LB_INFO1)
            info2 = job.getDescendantOfType(LineType.LB_INFO2)
            info_text = info1.text
            if info2: info_text = info_text + '\n' + info2.text
            info_text = info_text.strip().title()
            body.append(odf.Paragraph(info_text))
            
            # Write lb parts
            # TODO some ability parts are not getting properly bolded; blame line breaks
            # TODO Colossus is missing an ability
            parts = lb.getAllDescendantsOfType(LineType.LB_PART)
            writer.writeLbParts(parts, j_class)
            
            # Cards for job abilities
            abilities = job.getAllDescendantsOfType(LineType.ABILITY)
            for ab in abilities:
                # Title
                body.append(odf.Paragraph(ab.text.upper(), style = j_class + ' Ability'))
                
                # Job tag
                p = odf.Paragraph(j_name.title() + ' Ability')
                p.set_span('Italics', regex = '.*')
                body.append(p)
                
                # Info line(s)
                info = ab.getDescendantOfType(LineType.AB_INFO)
                info_text = info.text.strip().title()
                body.append(odf.Paragraph(info_text))
                
                # Write parts
                parts = ab.getAllDescendantsOfType(LineType.AB_PART)
                writer.writeAbilityParts(parts, j_class)
                
            # Cards for job talents
            talents = job.getAllDescendantsOfType(LineType.TALENT)
            for t in talents:
                t_name = t.text
                t_body.append(odf.Paragraph(t_name, style = j_class + ' Talent'))
                
                p = odf.Paragraph(j_name.title() + ' Talent')
                p.set_span('Italics', regex = '.*')
                t_body.append(p)
                
                t_rules = t.getDescendantOfType(LineType.TALENT_RULES)
                t_body.append(odf.Paragraph(t_rules.text))
        
    # Wowee
    doc_utils.save_doc(doc, 'icon_cards.odt')
    talent_doc.save('talent_cards.odt', pretty=True)


class BlockWriter:
    
    ab_part_key_regex = '([\\w\\W]+?) {0,1}[d\\d]*(?:\\[x\\]){0,1}[:\\.] .+'


    def __init__(self, body):
        self.doc_body = body
    
    def writeAbilityParts(self, parts, j_class):
        self.writeParts(parts, LineType.AB_PART, j_class)
    
    def writeLbParts(self, parts, j_class):
        self.writeParts(parts, LineType.LB_PART, j_class)
    
    def writeParts(self, parts, type, j_class):
        for part in parts:
            part_type = type
            rules_type = {
                LineType.LB_PART: LineType.LB_RULES,
                LineType.AB_PART: LineType.AB_RULES,
            }[type]
            s_item_type = {
                LineType.LB_PART: LineType.SUB_LB,
                LineType.AB_PART: LineType.SUB_ABILITY
            }[type]
            s_part_type = {
                LineType.LB_PART: LineType.SLB_PART,
                LineType.AB_PART: LineType.SAB_PART
            }[type]
            s_rules_type = {
                LineType.LB_PART: LineType.SLB_RULES,
                LineType.AB_PART: LineType.SAB_RULES
            }[type]
            s_info_type = {
                LineType.LB_PART: LineType.SLB_INFO,
                LineType.AB_PART: LineType.SAB_INFO
            }[type]
            
            
            text = part.text
            rules = part.getAllDescendantsOfType(rules_type)
            
            rules_text = ''
            if rules:
                for rule in rules:
                    rules_text = rules_text + ' ' + rule.text
            
            if rules_text: text = text + ' ' + rules_text
            p = odf.Paragraph(Styler.fix_spaces(text.strip()))
            
            # Identify part key
            m = re.match(BlockWriter.ab_part_key_regex, part.text.lower())
            key = m[1]
            
            # Bold ability part key
            p.set_span('Bold', regex = '(?i)^'+key)
            self.doc_body.append(p)
            
            # Render sub-items of this ability part after all part & rules text
            sub_item = part.getDescendantOfType(s_item_type)
            if sub_item:
                sub_name = sub_item.text
                self.doc_body.append(odf.Paragraph(sub_name.strip().title(), style = j_class + ' Sub-item'))
                
                sub_info = sub_item.getDescendantOfType(s_info_type)
                if sub_info:
                    self.doc_body.append(odf.Paragraph(sub_info.text.strip(), style = 'Sub-item'))
                
                sub_parts   = sub_item.getAllDescendantsOfType(s_part_type)
                for sub_part in sub_parts:
                    text = sub_part.text
                    sub_rules   = sub_part.getAllDescendantsOfType(s_rules_type)
                    if sub_rules:
                        for rule in sub_rules:
                            text = text + ' ' + rule.text
                    p = odf.Paragraph(Styler.fix_spaces(text.strip()), style = 'Sub-item')
                    
                    # Identify part key
                    m = re.match(BlockWriter.ab_part_key_regex, sub_part.text.lower())
                    key = m[1]
                    
                    # Bold ability part key
                    p.set_span('Bold Sub-item', regex = '(?i)^'+key)
                    self.doc_body.append(p)

class JobClass(Enum):
    STALWART    = 'Stalwart'
    VAGABOND    = 'Vagabond'
    MENDICANT   = 'Mendicant'
    WRIGHT      = 'Wright'

class Styler:
    job_num = 0
    
    def get_style(type):
        if type == LineType.JOB:
            c = Styler.get_class()
            Styler.job_num = Styler.job_num + 1
            return c.value + ' Job'
        if type == LineType.ABILITY:
            c = Styler.get_class()
            return c.value + ' Ability'
        # TODO implement more of this
    
    def get_job_class_for_soul(soul):
        return Styler.SOUL_CLASS_DICT[soul]
    
    # Hack; theoretically not necessary but need quicker turnaround
    def fix_spaces(str):
        str = re.sub(' +', ' ', str)
        # TODO does not work lol
        str = re.sub('(?m)\\n +', '\\n', str)
        return str
    
    SOUL_CLASS_DICT = {
        'KNIGHT'    : JobClass.STALWART,
        'WARRIOR'   : JobClass.STALWART,
        'BERSERKER' : JobClass.STALWART,
        'MERCENARY' : JobClass.STALWART,
        
        'SHADOW'    : JobClass.VAGABOND,
        'GUNNER'    : JobClass.VAGABOND,
        'THIEF'     : JobClass.VAGABOND,
        'RANGER'    : JobClass.VAGABOND,
        
        'ORACLE'    : JobClass.MENDICANT,
        'MONK'      : JobClass.MENDICANT,
        'WITCH'     : JobClass.MENDICANT,
        'BARD'      : JobClass.MENDICANT,
        
        'FLAME'     : JobClass.WRIGHT,
        'EARTH'     : JobClass.WRIGHT,
        'BOLT'      : JobClass.WRIGHT,
        'WATER'     : JobClass.WRIGHT,
    }

if __name__ == '__main__':
    main()