from dataclasses import Field

# Pierwszy poziom - root
tree = {
    "EW": ["Dokumentacja projektowa", "Dokumentacja odbiorowa", "Dokumentacja powykonawcza", "Dokumenty niesklasyfikowane"],
    "EWP": ["Dokumentacja odbiorowa", "Dokumentacja powykonawcza", "Dokumenty niesklasyfikowane"],
    "EWS": ["Dokumentacja odbiorowa", "Dokumentacja powykonawcza", "Dokumenty niesklasyfikowane"],
    "EKS": ["Dokumentacja odbiorowa1", "Dokumentacja powykonawcza1", "Dokumenty niesklasyfikowane"],
    "KSA": ["Podłączenia KS"],
    "NI": ["Numery inwentarozwe"],
    "UL": ["Uzgodnienia lokalizacji"],
    "N": ["Dokumenty niesklasyfikowane"]
}

# Drugi poziom
second_level = {
    "Dokumentacja projektowa": ["Projekty tekstowe", "Projekty graficzne"],
    "Dokumentacja odbiorowa": ["Zgłoszenie rozpoczęcia robót", "Notatki z robót zanikowych", "Szkice do robót zanikowych", "Wyniki badania wody", "Wyniki prób ciśnieniowych", "Dokument tekstowy", "Multimedia", "Mapa z zakresem monitoringu"],
    "Dokumentacja odbiorowa1": ["Zgłoszenie rozpoczęcia robót", "Notatki z robót zanikowych (otwarty wykop)", "Szkice do robót zanikowych", "Dokument tekstowy", "Multimedia", "Mapa z zakresem monitoringu"],
    "Dokumentacja powykonawcza": ["Protokoły odbioru końcowego sieci wodociągowej", "Protokoły odbioru sieci kanalizacji sanitarnej", "Protokoły odbioru końcowego przyłączy", "Mapy pomiaru powykonawczego sieci", "Mapy pomiaru powykonawczego przyłaczy"],
    "Dokumentacja powykonawcza1": ["Protokoły odbioru końcowego", "Protokoły odbioru końcowego przyłączy", "Mapy pomiaru powykonawczego sieci", "Mapy pomiaru powykonawczego przyłaczy"],
    "Dokumenty niesklasyfikowane": ["Dokumenty niesklasyfikowane"],
    "Podłączenia KS": ["Notatka z podłączennia do kanalizacji sanitarnej"],
    "Numery inwentarozwe": ["Księgi Inwentarzowe", "Protokół Przekazania do Eksploatacji", "Protokół Zdawczo-Odbiorczy przekazania w dzierżawę", "PZO", "PL - protokoły likwidacji", "OT", "PU", "PZOU", "PT"],
    "Uzgodnienia lokalizacji": ["L-", "LOK"]
}


def generate_file_name_tags(folderType, groupType, subGroupType):
    folder_index = list(tree.keys()).index(folderType)
    f = chr(folder_index + 65)

    group_index = tree[folderType].index(groupType)
    s = chr(group_index + 65)

    sub_group_index = second_level[groupType].index(subGroupType)
    t = chr(sub_group_index + 65)

    return f, s, t


def get_group(value):
    return tree.get(value)

def get_subgroup(value):
    return second_level.get(value)
