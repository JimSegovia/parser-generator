import re
def procesar_gramatica(entrada, codigos_terminales):
    if codigos_terminales is None:
        raise ValueError("❌ Debes proporcionar un diccionario con los códigos de los terminales.")

    producciones = []
    no_terminales = set()
    terminales = set()

    # Unir líneas que continúan
    lineas = []
    buffer = ""
    for linea in entrada.strip().split('\n'):
        linea = linea.strip()
        if not linea:
            continue
        if '→' in linea or '->' in linea:
            if buffer:
                lineas.append(buffer)
            buffer = linea
        else:
            buffer += ' ' + linea
    if buffer:
        lineas.append(buffer)

    # Procesar producciones
    for linea in lineas:
        if '→' in linea:
            izquierda, derecha = map(str.strip, linea.split('→'))
        else:
            izquierda, derecha = map(str.strip, linea.split('->'))

        no_terminales.add(izquierda)

        alternativas = [alt.strip() for alt in derecha.split('|')]
        for alt in alternativas:
            alt = alt.strip()
            if alt == 'λ':
                simbolos = []  # Producción vacía
            else:
                simbolos = re.findall(r'<[^<>]+>|[^\s]+', alt)

            producciones.append((izquierda, simbolos))
            for simbolo in simbolos:
                if re.match(r'<[^<>]+>', simbolo):
                    no_terminales.add(simbolo)
                else:
                    terminales.add(simbolo)

    # Asignar códigos faltantes automáticamente
    codigo_actual = max(codigos_terminales.values(), default=599) + 1
    for t in sorted(terminales):
        if t not in codigos_terminales:
            codigos_terminales[t] = codigo_actual
            print(f"⚠️ Terminal '{t}' no estaba codificado. Asignado código {codigo_actual}.")
            codigo_actual += 1

    # Mostrar no terminales
    print("No terminales:")
    print('|'.join(sorted(no_terminales)))

    # Mostrar terminales codificados en formato '|'
    print("\nTerminales (formato codigo para copiar):")
    print('|'.join(str(codigos_terminales[t]) for t in sorted(terminales)))

    # Mostrar terminales en formato '|'
    print("\nTerminales:")
    print(' , '.join(sorted(terminales)))

    # Mostrar producciones con códigos
    print("\nProducciones (con terminales codificados):")
    for izquierda, simbolos in producciones:
        reemplazada = []
        for s in simbolos:
            if s in codigos_terminales:
                reemplazada.append(str(codigos_terminales[s]))
            else:
                reemplazada.append(s)
        print(f"{izquierda}→{' '.join(reemplazada)}")


# INGRESAR AQUI SU GRAMATICA, SEPARADA POR ESPACIOS PARA CADA ELEMENTO
entrada = """
<S>→C <Z> V
<Z>→ <D> ; <Z> | <M> <Z> |  <G> <Z> | λ
<D>→ <ListaIds> : <Tipo>  | λ
<ListaIds> → id <ListaIdsCont> 
<ListaIdsCont> → , <ListaIds> | λ
<Tipo> → E | R
<M>→ id = <B> ;
<B>→ <T> <X>
<X>→ + <T> <X>  | λ
<T>→ <F> <Y>
<Y>→ * <F> <Y> | λ
<F>→ id  |  ( <B> ) | k | f
<G> → L ( <ListaIds> ) ;  | P ( <ListaIds> ) ;
"""
# INGRESAR AQUI LOS TOKENS PARA SUS VALORES TERMINALES
codigos_terminales = {
    'k': 300,
    'f': 301,
    'id': 100,
    'C': 400,
    'V': 401,
    'E': 402,
    'R': 403,

    'L': 404,
    'P': 405,

    ',': 200,
    ';': 201,
    '=': 202,
    '*': 203,
    '+': 204,
    '(': 205,
    ')': 206,
    ':': 207
}

procesar_gramatica(entrada, codigos_terminales)
