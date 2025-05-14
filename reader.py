#!/usr/bin/env python
# coding: utf-8

from copy import deepcopy
import re
import sys
try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree
import pyperclip
import json

from colors import get_shader_list, get_color_dict

OS = "linux"

if OS == "windows":
    baseloc = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Caves of Qud\\CoQ_Data\\StreamingAssets\\Base'
    slash = "\\"
else:
    baseloc = "/home/(you)/.steam/steam/steamapps/common/Caves of Qud/CoQ_Data/StreamingAssets/Base"
    slash = "/"


# Helper Functions

def argsfortype(xmltype):
    if (xmltype == "conversation"):
        return ["name"]  # TODO: add optional "title" argument override
    elif (xmltype == "colors" or xmltype == "bodyparts" or xmltype == "colorscss"):
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

def textof(node):
    if (t:=node.find("text")) is not None:
        result = t.text
    else:
        result = node.text
    if result is None:
        return ''
    else:
        return result

conditions = {
    'IfFinishedQuest': lambda q: f"the player has completed [[{q}]]",
    'IfFinishedQuestStep': lambda q: f"the player has completed [[{q.split('~')[0]}#{q.split('~')[1]}|{q.split('~')[1]}]]",
    'IfHaveActiveQuest': lambda q: f"[[{q}]] is active",
    'IfHaveBlueprint': lambda q: "the player is carrying {{f|" + q + "}} TODO make noun definite if needed",
    'IfHaveObservation': lambda q: f"the player has learned that TODO[explain {q}]",
    'IfHavePart': lambda q: "the player has {{f|" + q + "}}", # this is currently only used for mutations, may need to change in future
    'IfHaveQuest': lambda q: f"the player has accepted [[{q}]]",
    'IfHaveState': lambda q: f"TODO[explain what condition {q} is]",
    'IfHaveSultanNoteWithTag': lambda q: f"the player has learned that TODO[explain {q}]",
    'IfHaveText': lambda q: f"the option above contains the text {q} TODO delete if this is not true",
    'IfHaveVillageNote': lambda q: f"the player has learned that TODO[explain {q}]",
    'IfHindriarch': lambda q: f"{q} is Hindriarch",
    'IfLastChoice': lambda q: f"the last choice taken was {q} TODO restructure this",
    'IfLevelLessOrEqual': lambda q: f"the player's level is less than or equal to {q}",
    'IfNotFinishedQuest': lambda q: f"the player hasn't completed [[{q}]]",
    'IfNotFinishedQuestStep': lambda q: f"the player hasn't completed [[{q.split('~')[0]}#{q.split('~')[1]}|{q.split('~')[1]}]]",
    'IfNotHaveObservation': lambda q: f"the player hasn't learned that TODO[{q}]",
    'IfNotHavePart': lambda q: "the player doesn't have {{f|" + q + "}}", # this is currently only used for mutations, may need to change in future
    'IfNotHaveQuest': lambda q: f"the player hasn't accepted [[{q}]]",
    'IfNotHaveState': lambda q: f"TODO[explain what condition not having {q} is]",
    'IfNotReputationAtLeast': lambda q: f"the player's reputation isn't at least {q}",
    'IfNotSlynthCandidate': lambda q: f"[[{q}]] isn't a candidate for the [[Slynth]] settlement TODO grammar",
    'IfNotWearingBlueprint': lambda q: "the player is not wearing {{f|" + q + "}} TODO grammar",
    'IfReputationAtLeast': lambda q: f"the player's reputation is at least {q}",
    'IfSlynthCandidate': lambda q: f"[[{q}]] is a candidate for the [[Slynth]] settlement TODO grammar ",
    'IfSlynthChosen': lambda q: f"[[{q}]] was chosen for the [[Slynth]] settlement TODO grammar",
    'IfSpeakerHavePart': lambda q: f"TODO[explain the condition of the speaker having {q} part]",
    'IfSpeakerHaveTagOrProperty': lambda q: f"TODO[explain the condition of the speaker having {q} tag/prop]",
    'IfSpeakerNotHaveProperty': lambda q: f"TODO[explain the condition of the speaker not having {q} prop]",
    'IfTestState': lambda q: f"TODO[explain what condition test state {q} is]",
    'IfTrueKin': lambda q: "the player is a [[True Kin]]",
    'IfWearingBlueprint': lambda q: "the player is wearing {{f|" + q + "}} TODO grammar",
}

class Replacer:
    def __init__(self, trust=True) -> None:
        try:
            with open('replacements.json', 'r', encoding='utf-8') as file:
                if trust:
                    self.confirmed_replacements = json.load(file)
                    self.saved_replacements = {}
                else:
                    self.saved_replacements = json.load(file)
                    self.confirmed_replacements = {}
        except:
            print('Could not load replacements.json')
            self.saved_replacements = {}
            self.confirmed_replacements = {}
    
    def get(self, key, sentence=''):
        if key in self.confirmed_replacements:
            answer = self.confirmed_replacements[key]
        elif key in self.saved_replacements:
            answer = self.saved_replacements[key]
            confirm = input(f'Got saved answer of "{answer}" for {key}; hit Enter to confirm or input new answer')
            if confirm == '':
                answer = confirm
            self.confirmed_replacements[key] = answer
        else:
            print('Enter a replacement for the TODO block in this statement:')
            if sentence:
                prompt = sentence + '\n'
            else:
                prompt = key + '\n'
            answer = input(prompt)
            self.confirmed_replacements[key] = answer
        with open('replacements.json', 'w', encoding='utf-8') as file:
            json.dump(self.saved_replacements | self.confirmed_replacements, file)
        return answer


replacements = Replacer()
 
def getcondition(node):
    requirements = []
    todo_block = re.compile(r'TODO\[[^\]]*\]')
    for attr, val in node.attrib.items():
        if attr in conditions:
            cond = conditions[attr](val)
            # match = re.search(todo_block, cond)
            # print(cond, '|', match)
            if match := re.search(todo_block, cond):
                todotext = match.group()
                answer = replacements.get(todotext, cond)
                cond = re.sub(todo_block, answer, cond)
                # print(f'Replacing {todotext} with {cond}')
            requirements.append(cond)
    if requirements:
        return 'Only available if ' + ' and '.join(requirements)
    else:
        return None

def toconvo(node, title=None, ids=None):
    # {{Qud dialogue|nodetitle= | text= | title= }}
    condition = getcondition(node)
    trimmedtextarr = textof(node).splitlines()
    for i in range(0, len(trimmedtextarr)):
        trimmedtextarr[i] = trimmedtextarr[i].strip()
    trimmedtext = '\n'.join(trimmedtextarr)
    if condition:
        qdialoguetbl = [f'|nodetitle={node.get("ID")} ({condition})']
    else:
        qdialoguetbl = [f'|nodetitle={node.get("ID")}']
    qdialoguetbl.append(f'|text={replaceshaders(trimmedtext.strip())}')
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
            if n.get('Load', '') == 'Remove':
                for c in node.iter('choice'):
                    #starfungus: this if statement is confusing to me. it seemed to only ever break things
                    #so i made it check to see if the c GoToID is None first. this seemed to stop the breaking
                    #but i don't know if it works as intended?
                    if c.get('GoToID') == n.get('Target') and c.get('GoToID') is not None:
                        print('Removing', c.get('GoToID'), 'from', c.getparent().get('ID', 'unknown'))
                        node.remove(c)
                print('Done removing', n.get('Target'), 'from', n.getparent().get('ID', 'unknown'))
                node.remove(n)
            #check for both GoToID and Target, because they're synonyms.
            #this bit removes choices that point to the current node's ID, which is most common when
            #they get inherited. They are not visible in-game
            if n.get('GoToID') == node.get('ID') and n.get('GoToID') is not None:
                print('Removing self-referential', n.get('GoToID'), 'from', n.getparent().get('ID', 'unknown'))
                node.remove(n)
            if n.get('Target') == node.get('ID') and n.get('Target') is not None:
                print('Removing self-referential', n.get('Target'), 'from', n.getparent().get('ID', 'unknown'))
                node.remove(n)
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
                #check for both GoToID and Target, because they're synonyms.
                if n.get("GotoID") is not None:
                    row = [f'|tonode={n.get("GotoID")}',
                           f'|text={textof(n).strip()}']
                else:
                    row = [f'|tonode={n.get("Target")}',
                           f'|text={textof(n).strip()}']
                condition = getcondition(n)
                if condition:
                    row.append(f'|comment={condition}')
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
    return re.sub('({{)\s*([^}]+\s*\|[^}]*}})', '\\1Qud shader no parse|\\2', text, flags=re.S)

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
            value = '\', \''.join(temp[e])
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

def getshaderlist(root, args):
    return get_shader_list(root)

def getcolortable(root, args):
    temp = get_color_dict(root)
    return dictconversion(temp, 2)

def getconversation(root, args):
    tbl = ['{{Missing info|May need to be ordered properly, also needs TODOs filled in}}', '{{tocright}}']
    # tbl = []
    ids = {}
    if 'title' in args:
        title = args['title']
    else:
        title = None
    for conv in root.iter('conversation'):
        if (conv.get('ID') == args['name']):
            nodes = {}
            for node in conv.iter('node', 'start'):
                nodes[node.get('ID')] = node
            for node in conv.iter('node', 'start'):
                inherits = node.get('Inherits', '')
                if inherits in nodes:
                    # print(node.get('ID'), 'inherits', inherits)
                    for c in nodes[inherits].iter('choice', 'text'):
                        if c.tag != 'text' or node.find('text') is None:
                            node.append(deepcopy(c))
            try:
                for node in conv.iter('start'):
                    tbl.append(toconvo(node, title, ids))
                for node in conv.iter('node'):
                    tbl.append(toconvo(node, title, ids))
            except AttributeError as e:
                print(f"Got attribute error on {conv.get('ID')}:{node.get('ID')}: {e}")
                return ''
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

def main(tabletype, args):
    function = lambda x: 'function is not set'
    filename = ''
    if tabletype =='encounter':
        filename = f'{slash}EncounterTables.xml'
        function = getencountertable
    elif tabletype == 'colors':
        filename = f'{slash}Colors.xml'
        function = getcolortable
    elif tabletype == "colorscss":
        filename = f"{slash}Colors.xml"
        function = getshaderlist
    elif tabletype == 'conversation':
        filename = f'{slash}Conversations.xml'
        function = getconversation
    elif tabletype == 'population':
        filename = f'{slash}PopulationTables.xml'
        function = getpopulationtable
    elif tabletype == 'bodyparts':
        filename= f'{slash}Bodies.xml'
        function = getbodytypevariants
    elif tabletype == 'anatomies':
        filename= f'{slash}Bodies.xml'
        function = getanatomies
    else:
        raise ValueError(f'{tabletype} is not a valid table type; '
                         'use encounter, colors, conversation, population, bodyparts, and anatomies')
    r = getbaseroot(baseloc, filename)
    output = function(r, args)
    with open('output.txt', 'w', encoding='utf-8') as file:
        file.write(output)
        file.write('\n')
    print("Output saved in output.txt")
    pyperclip.copy(output)
    print("Output copied into clipboard.")
    # print(output)

# Main Function

if __name__ == '__main__':
    if len(sys.argv) > 1:
        xmltype = sys.argv[1]
    else:
        xmltype = input('Read from which table: [encounter|colors|conversation|population|bodyparts|anatomies]:\n')
    args = {}
    for i, arg in enumerate(argsfortype(xmltype)):
        if len(sys.argv) > 2 + i:
            inputstr = sys.argv[2+i]
        else:
            inputstr = input(f'Input {arg}: ')
        args.update({arg: inputstr})
    main(xmltype, args)


