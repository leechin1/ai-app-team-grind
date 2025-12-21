from google.genai import types
print(dir(types.Part))
try:
    print(help(types.Part.from_text))
except:
    pass
