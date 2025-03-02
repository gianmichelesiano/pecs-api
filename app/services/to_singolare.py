def to_singolare(parola, lingua):
    lingua = lingua.lower()
    
    if lingua == "en":
        import inflect
        p = inflect.engine()
        risultato = p.singular_noun(parola)
        return risultato if risultato else parola
        
    elif lingua == "it":
        # Regole semplificate per l'italiano
        if parola.endswith('i'):
            return parola[:-1] + 'o'
        elif parola.endswith('e'):
            return parola[:-1] + 'a'
        elif parola.endswith('ni'):
            return parola[:-1]
        else:
            return parola
            
    elif lingua == "de":
        # Regole semplificate per il tedesco
        if parola.endswith('en'):
            return parola[:-2]
        elif parola.endswith('er'):
            return parola[:-2]
        elif parola.endswith('e'):
            return parola[:-1]
        else:
            return parola
    
    elif lingua == "fr":
        # Regole semplificate per il francese
        if parola.endswith('s'):
            return parola[:-1]
        elif parola.endswith('aux'):
            return parola[:-3] + 'al'
        elif parola.endswith('ux'):
            return parola[:-2] + 'l'
        else:
            return parola
    
    elif lingua == "es":
        # Regole semplificate per lo spagnolo
        if parola.endswith('es') and len(parola) > 3:
            if parola[-3] in 'sz':
                return parola[:-2]
            return parola[:-2]
        elif parola.endswith('s'):
            return parola[:-1]
        else:
            return parola
    
    else:
        return "Lingua non supportata"


