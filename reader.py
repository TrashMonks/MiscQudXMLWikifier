import xml.etree.ElementTree as etree

def wikilang(attrname):
    if attrname == "Chance":
        return "weight"
    elif attrname == "Number":
        return "quantity"
    elif attrname == "Blueprint":
        return "item"
    elif attrname == "Table":
        return "table"
    else:
        return "error"
    
def torow(n):
    result = []
    for k in n:
        if k == "Blueprint":
            temp = '{{ID to page|' + n[k] + '}} '
        elif k == "Builder":
            continue
        else:
            temp = n[k]
        result.append(wikilang(k) + '=' + temp) 
    return '{{EncounterTable/Row|' + '|'.join(result) + '}}'

def totemplate(node):
    objectarr = []
    tablearr = []
    for n in node.iter('object'):
        objectarr.append(torow(n.attrib))
    for n in node.iter('tableobject'):
        tablearr.append(torow(n.attrib))
    merged = objectarr + tablearr
    finalresult = '\n|'.join(merged)
    return '{{EncounterTable\n|' + finalresult + '\n}}' + '\n<noinclude>[[Category:Encounter Tables]]</noinclude>'

et = etree.parse('REPLACEfilepath hereREPLACE')
root = et.getroot()

for node in root.iter('encountertable'):
    if (node.attrib.get('Name') == 'REPLACETablenameREPLACE'):
        print(totemplate(node))
