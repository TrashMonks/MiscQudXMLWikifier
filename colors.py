css_vars = {
    "r": "r-dark",
    "R": "r",
    "o": "o-dark",
    "O": "o",
    "w": "w-dark",
    "W": "w",
    "g": "g-dark",
    "G": "g",
    "b": "b-dark",
    "B": "b",
    "c": "c-dark",
    "C": "c",
    "m": "m-dark",
    "M": "m",
    "k": "k-dark",
    "K": "k",
    "y": "y-dark",
    "Y": "y"
}
def get_color_dict(node):
    d = {}
    for n in node.iter('shader'):
        d[n.get('Name')] = [n.get('Colors'), n.get('Type')]
    return d

def get_shader_list(root) -> str:
    output = []
    solids = {"R": [".qud-text.r" ],
                "r": [".qud-text.r-dark"],
                "O": [".qud-text.o"],
                "o": [".qud-text.o-dark"],
                "W": [".qud-text.w"],
                "w": [".qud-text.w-dark"],
                "G": [".qud-text.g"],
                "g": [".qud-text.g-dark"],
                "C": [".qud-text.c"],
                "c": [".qud-text.c-dark"],
                "B": [".qud-text.b"],
                "b": [".qud-text.b-dark"],
                "M": [".qud-text.m"],
                "m": [".qud-text.m-dark"],
                "Y": [".qud-text.y"],
                "y": [".qud-text.y-dark"],
                "K": [".qud-text.k"],
                "k": [".qud-text.k-dark"],
                }
    for n in root.iter("solidcolor"):
        name = str(n.get("Name")).replace(" ", "-")
        color = n.get("Color")
        solids[color].append(f".qud-text.{name}")
    for n in root.iter('shader'):
        #n.get(name, colors, type)
        shader_name =str(n.get('Name')).replace(" ", "-")
        shader_type = n.get('Type')
        shader_sequence = str(n.get('Colors'))
        if shader_type == "solid" or len(shader_sequence) < 2:
            solids[shader_sequence[0]].append(f".qud-text.{shader_name}")
        elif shader_sequence and shader_type and shader_name:
            gradient_css = make_gradient(shader_sequence, shader_type, name=shader_name)
            header = f".qud-text.{shader_name} {{"
            complete = header + gradient_css + "}"
            output.append(complete)
        else:
            print("Something wasn't defined.")
    for solid in solids:
        header = f" {", ".join(solids[solid])} {{"
        gradient_css = make_gradient(solid, "solid")
        complete = header + gradient_css + "}"
        output.append(complete)
    return "\n".join(output)

def make_gradient(sequence:str, shader_type:str, name="") -> str:
    # Define behavior based on type
    chars = sequence.split('-')
    max_len = len(chars)
    
    output = []
    size = ""
    if shader_type == "bordered":
        gradient = f"{char_to_var(chars[1])} 0ch, " +\
                   f"{char_to_var(chars[1])} 1ch, " +\
                   f"{char_to_var(chars[0])} 1ch, " +\
                   f"{char_to_var(chars[0])} 100%"
        size = "calc(100% - 1ch)"

        output = [gradient]
    elif shader_type == "alternation":
        # artificially stretch size to fit name
        extra_chars = len(name)- max_len

        i = 0
        j = 0
        while i < max_len:
            stretch = 1
            char = char_to_var(chars[i])
            if extra_chars > 0:
                stretch = 2
                extra_chars -= 1
            output.append(f"{char} {j}ch, {char} {j+stretch}ch")
            i+=1
            j+=stretch
        size = f"{j}ch"
    elif shader_type == "solid":
        char = char_to_var(chars[0])
        output = [f"{char} 0%, {char} 100%"]
    else:
        # sequence.
        size = f"{max_len}ch"
        i = 0
        while i < max_len:
            char = char_to_var(chars[i])
            output.append(f"{char} {i}ch, {char} {i+1}ch")
            i+=1
    output_str =  f"background-image: linear-gradient(to right, {','.join(output)});"
    if size:
        output_str += f"\nbackground-size:{size};"
    return output_str

def char_to_var(char:str)-> str:
    return f"var(--qud-color-{css_vars[char]})"
