"""Generates dark_mode.svg / light_mode.svg (the static layout).
Edit INFO below, run `python make_svg.py`, commit. today.py only fills in the live numbers.
Dynamic rows are marked with an id; today.py swaps the value and re-pads the dots."""
from xml.sax.saxutils import escape

LINE_W = 58          # chars available for each info line
INFO_X, TOP, STEP = 25, 35, 22

# ("section", title) | ("row", key, value, id_or_None) | ("blank",)
INFO = [
    ("title", "animesh@anidotdev"),
    ("row", "Role", "Backend Developer", None),
    ("row", "Uptime", "0 years, 0 months, 0 days", "age_data"),
    ("row", "Host", "ABES Engineering College", None),
    ("row", "Kernel", "B.Tech, 2nd year", None),
    ("blank",),
    ("row", "Languages.Programming", "JavaScript, Golang, C++", None),
    ("row", "Languages.Computer", "SQL, Bash, YAML", None),
    ("row", "Languages.Real", "English, Hindi", None),
    ("blank",),
    ("row", "Stack.Cloud", "AWS", None),
    ("row", "Hobbies.Writing", "Systems, ML, Backend", None),
    ("blank",),
    ("section", "Contact"),
    ("row", "GitHub", "anidotdev", None),
    ("row", "LinkedIn", "anidotdev", None),
    ("row", "Medium", "@anidotdev", None),
    ("row", "Blog", "anidotdev.pages.dev", None),
    ("blank",),
    ("section", "GitHub Stats"),
    ("row", "Repos", "0", "repo_data"),
    ("row", "Repos.Contributed", "0", "contrib_data"),
    ("row", "Stars", "0", "star_data"),
    ("row", "Commits", "0", "commit_data"),
    ("row", "Followers", "0", "follower_data"),
    ("loc",),
]

THEMES = {
    "dark_mode.svg":  dict(bg="#161b22", fg="#c9d1d9", key="#ffa657", val="#a5d6ff", cc="#616e7f", add="#3fb950", dele="#f85149"),
    "light_mode.svg": dict(bg="#f6f8fa", fg="#24292f", key="#953800", val="#0a3069", cc="#c2cfde", add="#1a7f37", dele="#cf222e"),
}

def dots(budget, value_len):
    n = max(0, budget - value_len)
    return " " + "." * (n - 2) + " " if n > 2 else [" ", " ", ". "][n] if n < 3 else ""

def build(theme):
    t = THEMES[theme]
    out = []
    height = TOP + STEP * len(INFO) + 5
    out.append(f'<?xml version="1.0" encoding="UTF-8"?>')
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,Menlo,DejaVu Sans Mono,monospace" width="640" height="{height}" font-size="16px">')
    out.append("<style>@font-face{src:local('Consolas'),local('Consolas Bold');font-family:'ConsolasFallback';size-adjust:109%;}"
               f".key{{fill:{t['key']}}}.value{{fill:{t['val']}}}.add{{fill:{t['add']}}}.del{{fill:{t['dele']}}}.cc{{fill:{t['cc']}}}"
               "text,tspan{white-space:pre}</style>")
    out.append(f'<rect width="640" height="{height}" fill="{t["bg"]}" rx="15"/>')
    out.append(f'<text fill="{t["fg"]}" xml:space="preserve">')
    for i, item in enumerate(INFO):
        y = TOP + STEP * i
        kind = item[0]
        if kind in ("title", "section"):
            label = item[1] if kind == "title" else "- " + item[1]
            out.append(f'<tspan x="{INFO_X}" y="{y}">{escape(label)}</tspan> {"-" * max(3, LINE_W - len(label) - 1)}')
        elif kind == "row":
            _, key, value, rid = item
            budget = LINE_W - 2 - len(key) - 1
            d = dots(budget, len(value))
            idattr = f' id="{rid}"' if rid else ""
            dattr = f' id="{rid}_dots" data-pad="{budget}"' if rid else ""
            keyhtml = ".".join(f'<tspan class="key">{escape(p)}</tspan>' for p in key.split("."))
            out.append(f'<tspan x="{INFO_X}" y="{y}" class="cc">. </tspan>{keyhtml}:<tspan class="cc"{dattr}>{d}</tspan><tspan class="value"{idattr}>{escape(value)}</tspan>')
        elif kind == "loc":
            key = "Lines.of.Code"
            budget = LINE_W - 2 - len(key) - 1 - 22  # leave room for ( +add++, -del-- )
            keyhtml = ".".join(f'<tspan class="key">{p}</tspan>' for p in key.split("."))
            out.append(f'<tspan x="{INFO_X}" y="{y}" class="cc">. </tspan>{keyhtml}:<tspan class="cc" id="loc_data_dots" data-pad="{budget}"> .... </tspan>'
                       f'<tspan class="value" id="loc_data">0</tspan> ( <tspan class="add" id="loc_add">0</tspan><tspan class="add">++</tspan>, '
                       f'<tspan class="del" id="loc_del">0</tspan><tspan class="del">--</tspan> )')
    out.append("</text></svg>")
    return "\n".join(out)

if __name__ == "__main__":
    for name in THEMES:
        open(name, "w", encoding="utf-8").write(build(name))
        print("wrote", name)
