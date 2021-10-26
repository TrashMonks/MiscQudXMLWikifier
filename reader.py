#!/usr/bin/env python
# coding: utf-8

import xml.etree.ElementTree as etree
import re
import pyperclip


baseloc = 'C:\Program Files (x86)\Steam\steamapps\common\Caves of Qud\CoQ_Data\StreamingAssets\Base'


# Helper Functions

def argsfortype(xmltype):
    if (xmltype == "conversation"):
        return ["name"]  # TODO: add optional "title" argument override
    elif (xmltype == "colors" or xmltype == "bodyparts"):
        return []
    else:
        return ["name"]

def getbaseroot(baselocation, filename):
    et = etree.parse(baselocation + filename)
    root = et.getroot()
    return root

def wikilang(attrname):
    if attrname == "Chance":
        return "weight"
    elif attrname == "Number":
        return "quantity"
    elif attrname == "Blueprint":
        return "item"
    elif attrname == "Table":
        return "table"
    elif attrname == "Weight":
        return "weight"
    elif attrname == "Name":
        return "table"
    elif attrname == "chance":
        return "weight"
    else:
        return "error"
    
def torow(n):
    result = []
    for k in n:
        if k == "Blueprint":
            temp = '{{ID to page|' + n[k] + '}}'
        elif k == "Builder":
            continue
        elif k == "Hint":
            continue
        else:
            temp = n[k]
        result.append(wikilang(k) + '=' + temp) 
    return '{{EncounterTable/Row|' + '|'.join(result) + '}}'
        
def totemplate(node, template):
    objectarr = []
    tablearr = []
    for n in node.iter('object'):
        objectarr.append(torow(n.attrib))
    for n in node.iter('tableobject'):
        tablearr.append(torow(n.attrib))
    for n in node.iter('table'):
        tablearr.append(torow(n.attrib))
    merged = objectarr + tablearr
    finalresult = '{{'+ template + '\n|' +'\n|'.join(merged) + '\n}}'
    #finalresult += '\n<noinclude>[[Category:Encounter Tables]]</noinclude>'
    return finalresult

def tocolordict(node):
    d = {}
    for n in node.iter('shader'):
        d[n.get('Name')] = [n.get('Colors'), n.get('Type')]
    return d

def toconvo(node, title=None, ids=None):
    # {{Qud dialogue|nodetitle= | text= | title= }}
    trimmedtextarr = node.find("text").text.splitlines()
    for i in range(0, len(trimmedtextarr)):
        trimmedtextarr[i] = trimmedtextarr[i].strip()
    trimmedtext = '\n'.join(trimmedtextarr)
    qdialoguetbl = [f'|nodetitle={node.get("ID")}',
                    f'|text={replaceshaders(trimmedtext.strip())}']
    if title: 
        qdialoguetbl.append(f'|title={title}')
    qdialogue = '{{Qud dialogue' + "\n".join(qdialoguetbl) + '}}'
    
    # {{Qud dialogue:choice|
    # {{Qud dialogue:choice row|tonode=end
    # |text=testing, testing!|end= true}}
    # {{!}}-}} UseID
    finalqchoices = ""
    if True:
        qchoices = []
        nquests = 1
        for n in node.iter('choice'):
            if nquests > 1:
                qnum = 'quest2'
                snum = 'step2'
            else:
                qnum = 'quest'
                snum = 'step'
            row = []
            if n.get('UseID'):
                row = ids[n.get('UseID')]
            else:
                row = [f'|tonode={n.get("GotoID")}',
                       f'|text={n.text.strip()}']
                if n.get('CompleteQuestStep'):
                    quest, step = n.get('CompleteQuestStep').split('~')
                    row.append(f'|{qnum}={quest}|{snum}={step}')
                    nquests = 2
                elif n.get('FinishQuest'):
                    quest = n.get('FinishQuest')
                    row.append(f'|{qnum}={quest}|{snum}=reward')
                    nquests = 2
                elif n.get('StartQuest'):
                    quest = n.get('StartQuest')
                    row.append(f'|{qnum}={quest}|{snum}=accept')
                    nquests = 2
                convoid = n.get('ID')
                if convoid not in ids:
                    ids[convoid] = row
            qchoices.append('{{Qud dialogue:choice row\n' + '\n'.join(row) + '}}')
        
        finalqchoices = '{{Qud dialogue:choice|\n' + '\n{{!}}-\n'.join(qchoices) + '}}'
    return qdialogue + '\n' + finalqchoices

def replaceshaders(text):
    return re.sub('({{)\s*(.+\s*\|.*}})', '\\1Qud shader no parse|\\2', text)

def tobodypartvariantsdict(node):
    d = {}
    for n in node.iter('bodyparttypevariant'):
        d[n.get('Type')] = n.get('VariantOf')
    return d

def toanatomy(node):
    d = []
    for n in node.iter('part'):
        temp = {}
        temp['type'] = n.get('Type')
        if n.get('Laterality'):
            temp['laterality'] = n.get('Laterality')
        d.append(temp)
    return d

def dictconversion(temp, arglen):
    final = []
    for e in temp:
        parens = ['', '']
        if arglen > 1:
            parens = ['{', '}']
            value = ', '.join(temp[e])
        else:
            value = temp[e]
        final.append(f"['{e}'] = {parens[0]}'{value}'{parens[1]}")
    finalstr = ',\n'.join(final)
    return finalstr

def anatomytemplate(name, _type, laterality):
    s = f"{{{{Anatomy|name={name}\n|type={_type}"
    if laterality is not None:
        s += f"|laterality={laterality}"
    s += '}}'
    return  s
           


# Main "get" functions


def getencountertable(root, args):
    tbl = []
    for node in root.iter('encountertable'):
        if (node.attrib.get('Name') == args['name']):
            tbl.append(totemplate(node, 'EncounterTable'))
    return '\n'.join(tbl)

def getpopulationtable(root, args):
    tbl = []
    for node in root.iter('population'):
        if (node.attrib.get('Name') == args['name']):
            n = node.find('group')
            if n.get('Style') == 'pickeach':
                etstyle = '|roll=each'
            else:
                etstyle = '|roll=once'
            tbl.append(totemplate(n, 'EncounterTable' + etstyle))
    return f"=== {args['name']} ===\n" + '\n'.join(tbl)
    
def getcolortable(root, args):
    temp = tocolordict(root)
    return dictconversion(temp, 2)

def getconversation(root, args):
    tbl = []
    ids = {}
    if 'title' in args:
        title = args['title']
    else:
        title = None
    for node in root.iter('conversation'):
        if (node.attrib.get('ID') == args['name']):
            for n in node.iter('node'):
                tbl.append(toconvo(n, title, ids))
    return '\n'.join(tbl)

def getbodytypevariants(root, args):
    temp = tobodypartvariantsdict(root)
    return dictconversion(temp, 1)

def getanatomies(root, args):
    d = {}
    final = []
    for node in root.iter('anatomy'):
        d[node.get('Name')] = toanatomy(node)
    anatomy = []
    for a in d:
        for part in d[a]:
            anatomy.append(anatomytemplate(a, part['type'],
                part['laterality'] if ('laterality' in part) else None))
    final.append('\n'.join(anatomy))
    return '\n'.join(final)


# In[12]:


def main(tabletype, args):
    function = lambda x: 'function is not set'
    filename = ''
    if tabletype =='encounter':
        filename = '\EncounterTables.xml'
        function = getencountertable
    elif tabletype == 'colors':
        filename = '\Colors.xml'
        function = getcolortable
    elif tabletype == 'conversation':
        filename = '\Conversations.xml'
        function = getconversation
    elif tabletype == 'population':
        filename = '\PopulationTables.xml'
        function = getpopulationtable
    elif tabletype == 'bodyparts':
        filename= '\Bodies.xml'
        function = getbodytypevariants
    elif tabletype == 'anatomies':
        filename= '\Bodies.xml'
        function = getanatomies
    else:
        error('type not specified!')
    r = getbaseroot(baseloc, filename)
    output = function(r, args)
    pyperclip.copy(output)
    print(output)

# Main Function

xmltype = input('Read from which table: [encounter|colors|conversation|population|bodyparts|anatomies]:\n')
args = {}
for arg in argsfortype(xmltype):
    print(arg)
    inputstr = input(f'Input {arg}: ')
    args.update({arg: inputstr})

main(xmltype, args)
print("Output copied into clipboard.")



