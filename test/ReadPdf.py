from google import genai
from google.genai import types
import re, textwrap

def format(text, width=100):
    seen, out = set(), []
    for line in text.splitlines():
        line = line.strip()
        if not line or line in seen: continue
        seen.add(line)
        if re.match(r"^\d+\.\s", line):
            out.append(f"\n\033[1m{line}\033[0m")
        elif "**" in line:
            line = re.sub(r"\*\*(.+?)\*\*", lambda m: f"\033[1m{m.group(1)}\033[0m", line)
            out.append(textwrap.fill(line, width))
        elif line.startswith(("* ", "- ", "•")):
            out.append("  • " + line.lstrip("*•- "))
        else:
            out.append(textwrap.fill(line, width))
    return "\n".join(out)

client = genai.Client(api_key='AIzaSyC8BMMSq5kms0_3rd9Fvl_dRI3WZ1IDbZc')
with open(r"D:\Code\Python\AI\Agent_AI\JproChat\Python cơ bản.pdf", "rb") as f:
    pdf = f.read()

try:
    res = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[types.Part.from_bytes(data=pdf, mime_type='application/pdf'), "Chương 2 nói về cái gì?"]
    )
    print(format(res.text))
except Exception as e:
    print(f"Error: {e}")
