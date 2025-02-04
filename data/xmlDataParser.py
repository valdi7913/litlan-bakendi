from lxml import etree
import asyncpg
import asyncio
import re

async def insert_data(result):
    conn = await asyncpg.connect(
        database="litlandb",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )

    await conn.execute("DELETE FROM word")

    for word, definition in result:
        print(word, definition)
        await conn.execute(
            "INSERT INTO word(text, definition) VALUES($1, $2)", 
            word,
            definition
        )
    
    await conn.close()
    print("Data inserted successfully!")

def clean_text(text):
    # Define allowed Icelandic letters (upper & lowercase)
    ICELANDIC_ALPHABET = "AÁBDÐEÉFGHIÍJKLMNOÓPRSTUÚVXYÝÞÆÖaábðddeéfghiíjklmnoóprstuúvxyýþæö"

    # Compile regex pattern to remove all non-Icelandic letters
    pattern = f"[^{ICELANDIC_ALPHABET}]"  # Matches anything NOT in the Icelandic alphabet

    """Remove all spaces and non-Icelandic characters."""
    return re.sub(pattern, "", text)

def read_dictionary(file_path):
    tree = etree.parse(file_path)
    root = tree.getroot()
    ns = {'ns': 'http://localhost/xmlschema'}

    lemmas = []
    definitions = []

    lexical_entries = root.xpath('//ns:LexicalEntry', namespaces=ns)

    for entry in lexical_entries:

        feat = entry.find('.//ns:Lemma/ns:feat', namespaces=ns)
        word = feat.get("val")
        #trim non alphabetic numbers
        word = clean_text(word)
        word = word.lower()

        definitionElement = entry.find('.//ns:Sense/ns:Definition', namespaces=ns)

        # Handle the case where there is no definition
        definition = ""
        if not definitionElement is None:
            definition = definitionElement.get("text")

        if word is None:
            continue

        if definition is None:
            definition = ""

        if len(word) < 6:
            lemmas.append(word)
            definitions.append(definition)

    result = list(zip(lemmas, definitions))
    return result

file_path = "ISLEX_dict.xml"
# file_path = "islex_test.xml"

result = read_dictionary(file_path)
asyncio.run(insert_data(result))
