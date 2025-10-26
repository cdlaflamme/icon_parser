from pypdf import PdfReader
import re

"""
have heirarchy structure and node classes created
need to loop through content and start matching patterns
problems:
- remove page lines
- need to figure out how to identify every kind of line (rules vs flavor, mostly)
-- this is just based on whatever the previous type was
"""

def main():
    in_path = "icon2.pdf"
    
    reader = PdfReader(in_path)
    pages = reader.pages[37-1:39-1+1]
    
    line_types = []
    
    for page in pages:
        text = page.extract_text()
        lines = text.split("\n")
        
        parent_h_level = 99
        parent_type = None
        last_type = None
        
        for line in lines:
            
            type = None
            
            if (is_line_page_num(line)):
                type = "page_n"
            elif (is_line_soul(line)):
                type = "soul"
                parent_type = type
            elif (is_line_job(line)):
                type = "job"
                parent_type = type
            elif (is_line_ability(line)):
                type="ability"
                parent_type="ability"
            
            if type is None:
                if parent_type == "soul":
                    type = "flavor"
                elif parent_type == "job":
                    if is_line_all_caps(line):
                        type = "trait"
                        parent_type = type
                    else:
                        type = "flavor"
                elif parent_type == "trait":
                    type = "rules"
                elif parent_type == "abliity":
                    if last_type == "ability":
                        type = "ab info"
                    elif is_line_ab_part(line):
                        type = "ab part"
                        parent_type = "ab part"
                    else:
                        type = "flavor"
            
            #if we have encountered a line that is NOT under the previous parent, break out of it
            #equivalent to a min statement but I'm anticipating additional logic here
            line_h_level = h_dict[type]
            if  line_h_level < parent_h_level:
                parent_h_level = line_h_level
            last_type = type
            
            pair = (type, line)
            line_types.append(pair)
            print(str(parent_type) + str(pair))
                

heirarchy_dict = h_dict = {
    None: 999,
    "page_n": 999,
    "soul": 0,
    "flavor": 99,
    "job": 1,
    "trait": 2,
    "rules": 4,
    "reminder": 99,
    "ability": 2,
    "ab info": 3, 
    "ab part": 3,
    "limit break": 2
}

def is_line_page_num(line):
    m = re.match('Page\\W+of\\W+\\d*\\W+\\d*', line)
    return m is not None

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

def is_line_ab_part(line):
    # TODO
    #find colon; fetch text until colon; this is the "key"
    #match key to list of approved phrases
    #if any match, we have an ability part

if __name__ == "__main__":
	main()