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
    
    # every parent block is (nominally) a soul!
    for soul in blocks:
        
        # get each job within
        jobs = soul.getAllDescendantsOfType(LineType.JOB)
        
        for job in jobs:
            # card 1: job name, keyword, trait, limit break
            # - consider flavor on the back...
            
            # Job Name
            j_class = Styler.get_job_class_for_soul(job.soul).value
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
            
            # TODO sub trait parts like shrine, puppet and beast
            
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
            
            # Assemble ability parts
            parts = lb.getAllDescendantsOfType(LineType.LB_PART)
            
            # TODO some ability parts are not getting properly recognized; bundled in with line breaks and not bolded
            # TODO paradiso is cut off
            ab_part_key_regex = '([\\w\\W]+?) {0,1}[d\\d]*(?:\\[x\\]){0,1}[:\\.] .+'
            for part in parts:
                text = part.text
                rules = part.getDescendantOfType(LineType.LB_RULES)
                
                if rules: text = text + ' ' + rules.text
                p = odf.Paragraph(text.strip())
                
                # Identify part key
                m = re.match(ab_part_key_regex, part.text.lower())
                key = m[1]
                
                # Bold ability part key
                p.set_span('Bold', regex = '(?i)^'+key)
                body.append(p)
                
                # Render sub-items of this ability part after all part & rules text
                sub_lb = part.getDescendantOfType(LineType.SUB_LB)
                if sub_lb:
                    sub_name = sub_lb.text
                    body.append(odf.Paragraph(sub_lb.text.strip().title(), style = j_class + ' Sub-item'))
                    
                    sub_info = sub_lb.getDescendantOfType(LineType.SLB_INFO)
                    if sub_info: body.append(odf.Paragraph('\t' + sub_info.text.strip()))
                    
                    sub_parts   = sub_lb.getAllDescendantsOfType(LineType.SLB_PART)
                    for sub_part in sub_parts:
                        text = sub_part.text
                        sub_rules   = sub_part.getDescendantOfType(LineType.SLB_RULES)
                        if sub_rules: text = text + ' ' + sub_rules.text
                        
                        p = odf.Paragraph(text.strip(), style = 'Sub-item')
                        
                        # Identify part key
                        m = re.match(ab_part_key_regex, sub_part.text.lower())
                        key = m[1]
                        
                        # Bold ability part key
                        p.set_span('Bold Sub-item', regex = '(?i)^'+key)
                        body.append(p)
                        
            
            # cards for job abilities
            
            # cards for job talents
             # TODO create talent style
        
        
        # BELOW: OUTDATED
        """
        style = Styler.get_style(block.type)
        block.style = style
        
        p = odf.Paragraph(block.text, style = block.style)
        
        # Add page/colum break if starting new job/ability
        if block.type in [LineType.ABILITY]:
            #body.append(odf.ColumnBreak())
            pass
        elif block.type in [LineType.JOB]:
            body.append(odf.PageBreak())
        body.append(p)
        """
    # Wowee
    doc_utils.save_doc(doc, 'icon_cards.odt')

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