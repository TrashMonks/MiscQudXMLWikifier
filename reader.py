import xml.etree.ElementTree as etree
baseloc = 'C:\Program Files (x86)\Steam\steamapps\common\Caves of Qud\CoQ_Data\StreamingAssets\Base'

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

def todict(node):
    d = {}
    for n in node.iter('shader'):
        d[n.get('Name')] = [n.get('Colors'), n.get('Type')]
    return d

def toconvo(node, title=None):
    # {{Qud dialogue|nodetitle= | text= | title= }}
    qdialoguetbl = [f'|nodetitle={node.get("ID")}',
                    f'|text={node.find("text").text.strip()}']
    if title: 
        qdialoguetbl.append(f'|title={title}')
    qdialogue = '{{Qud dialogue' + "\n".join(qdialoguetbl) + '}}'
    
    # {{Qud dialogue:choice|
    # {{Qud dialogue:choice row|tonode=end
    # |text=testing, testing!|end= true}}
    # {{!}}-}} UseID
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
            row = [f'UseID: {n.get("UseID")}']
        else:
            row = [f'|tonode={n.get("GotoID")}',
                   f'|text={n.text.strip()}']
            if n.get('CompleteQuestStep'):
                quest, step = n.get('CompleteQuestStep').split('~')
                row.append(f'|{qnum}={quest}|{snum}={step}')
                nquests = 2
            elif n.get('FinishQuest'):
                quest = n.get('FinishQuest')
                row.append(f'|{qnum}={quest}|{snum}=rewards')
                nquests = 2
            elif n.get('StartQuest'):
                quest = n.get('StartQuest')
                row.append(f'|{qnum}={quest}|{snum}=accept')
                nquests = 2
        qchoices.append('{{Qud dialogue:choice row\n' + '\n'.join(row) + '}}')
        
    finalqchoices = '{{Qud dialogue:choice|\n' + '\n{{!}}-\n'.join(qchoices) + '}}'
    return qdialogue + '\n' + finalqchoices

def getencountertable(root, args):
    """
    returns a specific encountertable formatted for the wiki.
    NOTE: builders and hints are ignored
    
    args parameters:
      name   | the name of the encounter table
    """
    tbl = []
    for node in root.iter('encountertable'):
        if (node.attrib.get('Name') == args['name']):
            tbl.append(totemplate(node, 'EncounterTable'))
    return '\n'.join(tbl)


def getpopulationtable(root, args):
    """
    returns a specific population table formatted for the wiki.
    NOTE: builders and hints are ignored
    
    args parameters:
      name   | the name of the population table
    """
    tbl = []
    for node in root.iter('population'):
        if (node.attrib.get('Name') == args['name']):
            n = node.find('group')
            if n.get('Style') == 'pickeach':
                etstyle = '|roll=each'
            else:
                etstyle = '|roll=once'
            tbl.append(totemplate(n, 'EncounterTable' + etstyle))
    return '\n'.join(tbl)

def getcolortable(root, args):
    """
    returns the color templates formatted for the wiki.
    this doesn't use any args.
    """
    temp = todict(root)
    final = []
    for e in temp:
        final.append("['" + e + "']={'" + temp[e][0] + "', '" + temp[e][1] + "'},")
    finalstr = '\n'.join(final)
    return finalstr

def getconversation(root, args):
    """
    returns an entire conversation formatted for the wiki.

    NOTE: UseID is not implemented yet. please check to make sure all UseIDs are properly replaced! 
    args parameters:
      name   | the name of the convo id
      title  | (optional) the title to set. the wiki by default uses the base page title. 
               this is used if you want to override this.
    """
    tbl = []
    for node in root.iter('conversation'):
        if (node.attrib.get('ID') == args['name']):
            for n in node.iter('node'):
                tbl.append(toconvo(n, args['title'] or None))
    return '\n'.join(tbl)

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
    else:
        error('type not specified!')
    r = getbaseroot(baseloc, filename)
    print(function(r, args))
"""
main takes 2 (sort of) arguments:
  tabletype: the xml type you want to read: (encounter, colors, conversation)
  args: a dictionary of arguments to pass which depend on the table type you select.
"""
if __name__ = '__main__':
    args = {'name':'JoppaZealot',
       'title':'zealot of the Six Day Stilt'}
    main('conversation', args)
    
