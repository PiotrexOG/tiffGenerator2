from dataclasses import Field

first = ["EW", "EWP", "EWS", "EKS", "KSA", "PZO", "UL", "N"]
second = ["Dokumentacja projektowa", "Dokumentacja odbiorowa", "Dokumentacja powykonawcza","Dokumenty niesklasyfikowane"]

secondA = ["Projekty tekstowe", "Projekty graficzne"]
secondB = ["Zgłoszenie rozpoczęcia robót", "Notatki z robót zanikowych", "Szkice do robót zanikowych", "Wyniki badania wody", "Wyniki prób ciśnieniowych", "Dokument tekstowy", "Multimedia", "Mapa z zakresem monitoringu"]
secondC = ["Protokoły odbioru końcowego sieci wodociągowej","Protokoły odbioru sieci kanalizacji sanitarnej", "Protokoły odbioru końcowego przyłączy","Mapy pomiaru powykonawczego sieci", "Mapy pomiaru powykonawczego przyłaczy","Niesklasyfikowane"]
secondD = ["Dokumenty niesklasyfikowane"]

def generate_file_name_tags(folderType, groupType, subGroupType):
    f = chr(first.index(folderType) + 65)
    s = chr(second.index(groupType) + 65)
    t = 0
    if s == 'A':
        t = chr(secondA.index(subGroupType) + 65)
    elif s == 'B':
        t = chr(secondB.index(subGroupType) + 65)
    elif s == 'C':
        t = chr(secondC.index(subGroupType) + 65)
    else:
        t = chr(secondD.index(subGroupType) + 65)
    return f, s, t

def get_subgroup(value):
    if value == "Dokumentacja projektowa":
        subgroup_options = secondA
    elif value == "Dokumentacja odbiorowa":
        subgroup_options = secondB
    elif value == "Dokumentacja powykonawcza":
        subgroup_options = secondC
    elif value == "Dokumenty niesklasyfikowane":
        subgroup_options = secondD
    else:
        subgroup_options = []
    return subgroup_options

def get_group(value):
    if value in {"EW", "EWP", "EWS", "EKS"}:
        doc_type_options = second
    elif value in {"KSA", "PZO", "UL", "N"}:
        doc_type_options = second
    else:
        doc_type_options = []
    return doc_type_options
