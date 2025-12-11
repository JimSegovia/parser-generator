from collections import deque
from collections import OrderedDict
from pprint import pprint
import primerosysiguientes
from primerosysiguientes import production_list, nt_list as ntl, t_list as tl

nt_list = []
t_list = []

LAMBDA = 'λ'



class State:
    _id = 0

    def __init__(self, closure):
        self.closure = closure
        self.no = State._id
        State._id += 1


class Item(str):
    def __new__(cls, item, lookahead=list()):
        if '.' not in item:
            raise ValueError(f"Item mal formado, sin '.': {item}")
        self = str.__new__(cls, item)
        # Lookaheads are IGNORED for LR(0) identity
        self.lookahead = [] 
        return self

    def __str__(self):
        return super(Item, self).__str__()



def closure(items):
    def exists(newitem, items):
        # Only check the core item string since lookaheads are gone
        for i in items:
            if i == newitem:
                return True
        return False

    global production_list

    while True:
        flag = 0
        for i in items:
            head, body = i.split('→')
            symbols = split_body_with_dot(body.strip())

            if '.' not in symbols or symbols.index('.') == len(symbols) - 1:
                continue

            dot_pos = symbols.index('.')
            B = symbols[dot_pos + 1]  # símbolo después del punto

            if B not in nt_list:
                continue
            
            # LR(0): We DO NOT compute lookaheads from beta + la

            for prod in production_list:
                lhs, rhs = prod.split('→')
                if lhs.strip() != B:
                    continue

                rhs_symbols = rhs.strip().split()
                new_body = '. ' + ' '.join(rhs_symbols)
                new_item = Item(f"{B}→{new_body}", []) # Empty lookahead

                if not exists(new_item, items):
                    items.append(new_item)
                    flag = 1

        if not flag:
            break

    return items

def split_body_with_dot(body):
    result = []
    i = 0
    while i < len(body):
        if body[i] == '.':
            result.append('.')
            i += 1
        elif body[i] == ' ':
            i += 1  # ignora espacios extra
        else:
            sym = ''
            while i < len(body) and body[i] not in ['.', ' ']:
                sym += body[i]
                i += 1
            result.append(sym)
    
    # Filter out Lambda/Epsilon from the result to treat them as empty
    # But keep '.'
    # The generator uses 'λ' (from code constant/string)
    LAMBDA_SYMBOLS = ['λ', 'ε']
    filtered_result = [x for x in result if x not in LAMBDA_SYMBOLS]
    
    # Special case: If the body was JUST lambda/epsilon (now empty), we have [].
    # But we might have the dot.
    # If original was "A -> . λ", split gives ['.', 'λ']. Filtered gives ['.'].
    # If original was "A -> λ .", split gives ['λ', '.']. Filtered gives ['.']. 
    # This correctly reduces to "A -> ." 
    
    return filtered_result


def pretty_print_items(items, codigos_equivalentes={}):
    for item in items:
        # Remplaza '.' por '●' solo para mostrar
        item_str = item.replace('.', '●').replace('→', '->')

        # Reemplazar símbolos codificados por su forma legible
        if codigos_equivalentes:
            for codigo, texto in codigos_equivalentes.items():
                item_str = item_str.replace(codigo, texto)

        for lookahead in item.lookahead:
            lookahead_str = codigos_equivalentes.get(lookahead, lookahead) if codigos_equivalentes else lookahead
            print(f"[ {item_str}, {lookahead_str} ]")

def format_states_lr0(states, codigos_equivalentes={}, show_lambda=False, empty_symbol='λ'):
    result = []
    for idx, state in enumerate(states):
        result.append(f"Item{idx}{{")
        for item in state: # Access list directly
             
             head, body = item.split('→')
             
             # Sanitize body for display: Remove internal λ/ε if present
             for bad_sym in ['λ', 'ε']:
                 body = body.replace(bad_sym, "")
             
             # Handle dot and arrow
             body_display = body.replace('.', '●').strip()
             
             # If logic led to space issues, clean up multiple spaces
             body_display = " ".join(body_display.split())
             
             # Logic to show Lambda/Epsilon if body is effectively empty (only dot) and show_lambda is True
             if body_display.replace('●', '').strip() == "":
                 if show_lambda:
                     if body_display.startswith('●'):
                          body_display = f"● {empty_symbol}" 
                     else:
                          body_display = f"{empty_symbol} ●"
             
             # For LR(0), we DO NOT show lookaheads.
             
             line = f"[ {head} → {body_display} ]"
             result.append(line)
             
        result.append("}\n")
    return "\n".join(result)


def goto(items, symbol):
    initial = []

    for i in items:
        head, body = i.split('→')
        symbols = split_body_with_dot(body.strip())

        if '.' not in symbols:
            continue

        dot_pos = symbols.index('.')

        # Verificamos si hay símbolo después del punto
        if dot_pos + 1 < len(symbols) and symbols[dot_pos + 1] == symbol:
            # Mover el punto a la derecha del símbolo actual
            new_symbols = symbols[:dot_pos] + [symbol, '.'] + symbols[dot_pos + 2:]
            new_body = ' '.join(new_symbols)
            initial.append(Item(f"{head}→{new_body}", i.lookahead))

    return closure(initial)



def calc_states():
    def contains(states, t):

        for s in states:
            if len(s) != len(t): continue

            if sorted(s) == sorted(t):
                # For LR(0), we only care about core items (lookaheads are ignored)
                return True
                
                # Original CLR logic for reference:
                # for i in range(len(s)):
                #     if s[i].lookahead != t[i].lookahead: break
                # else:
                #     return True

        return False

    global production_list, nt_list, t_list

    head, body = production_list[0].split('→')

    states = [closure([Item(head + '→.' + body, [])])]

    while True:
        flag = 0
        for s in states:

            for e in nt_list + t_list:

                t = goto(s, e)
                if t == [] or contains(states, t): continue

                states.append(t)
                flag = 1

        if not flag: break

    return states


def make_table(states):
    global nt_list, t_list

    def getstateno(t):
        for s in states:
            if len(s.closure) != len(t):
                continue
            if sorted(s.closure) == sorted(t):
                for i in range(len(s.closure)):
                    if s.closure[i].lookahead != t[i].lookahead:
                        break
                else:
                    return s.no
        return -1

    def getprodno(item):
        head, body = item.split('→')
        body_without_dot = body.replace('.', '').strip()
        clean = head.strip() + '→' + body_without_dot
        for i, prod in enumerate(production_list):
            if prod.strip() == clean:
                return i
        return -1

    SLR_Table = OrderedDict()

    for i in range(len(states)):
        states[i] = State(states[i])  # Asigna números de estado

    for s in states:
        SLR_Table[s.no] = OrderedDict()

        for item in s.closure:
            head, body = item.split('→')
            body_symbols = split_body_with_dot(body.strip())


            if body_symbols == ['.']:  # Producción completamente reducida
                for term in item.lookahead:
                    if term not in SLR_Table[s.no].keys():
                        SLR_Table[s.no][term] = {'r' + str(getprodno(item))}
                    else:
                        SLR_Table[s.no][term] |= {'r' + str(getprodno(item))}
                continue

            try:
                dot_pos = body_symbols.index('.')
            except ValueError:
                raise ValueError(f"Producción inválida sin punto: {item}")

            if dot_pos == len(body_symbols) - 1:
                # Punto al final (producción lista para reducir)
                if getprodno(item) == 0:
                    SLR_Table[s.no]['$'] = 'Aceptar'
                else:
                    for term in item.lookahead:
                        if term not in SLR_Table[s.no].keys():
                            SLR_Table[s.no][term] = {'r' + str(getprodno(item))}
                        else:
                            SLR_Table[s.no][term] |= {'r' + str(getprodno(item))}
                continue

            # Punto no al final: shift o goto
            nextsym = body_symbols[dot_pos + 1]
            t = goto(s.closure, nextsym)
            if t != []:
                if nextsym in t_list:
                    if nextsym not in SLR_Table[s.no].keys():
                        SLR_Table[s.no][nextsym] = {'d' + str(getstateno(t))}
                    else:
                        SLR_Table[s.no][nextsym] |= {'d' + str(getstateno(t))}
                else:
                    SLR_Table[s.no][nextsym] = str(getstateno(t))

    return SLR_Table

def augment_grammar():
    for i in range(ord('Z'), ord('A') - 1, -1):
        new_start = chr(i)
        if new_start not in ntl:
            start_prod = production_list[0]
            production_list.insert(0, new_start + '→' + start_prod.split('→')[0])
            ntl[new_start] = primerosysiguientes.NonTerminal(new_start)  # <- Añadido
            return

import sys
def main():
    global production_list, ntl, nt_list, tl, t_list

    print("Ingresa los símbolos NO TERMINALES separados por |:")
    non_terminal_input = input().strip()
    non_terminal_symbols = non_terminal_input.split('|')

    primerosysiguientes.nt_list.clear()
    for nt in non_terminal_symbols:
        primerosysiguientes.nt_list[nt] = primerosysiguientes.NonTerminal(nt)

    print("\nIngresa los símbolos TERMINALES separados por |:")
    terminal_input = input().strip()
    terminal_symbols = terminal_input.split('|')

    primerosysiguientes.t_list.clear()
    for term in terminal_symbols:
        primerosysiguientes.t_list[term] = primerosysiguientes.Terminal(term)

    print("\nPega tus producciones (una por línea).")
    print("Cuando termines, presiona Enter en una línea vacía:")

    user_productions = []
    try:
        while True:
            line = input()
            if line.strip() == "":
                break
            user_productions.append(line.strip())
    except EOFError:
        pass  # Por si usas redirección o termina entrada con Ctrl+D (Linux/Mac)

    if not user_productions:
        print("No se ingresaron producciones. Finalizando.")
        return

    # Toda la salida en .txt
    with open("salida_clr1.txt", "w", encoding="utf-8") as f:
        original_stdout = sys.stdout
        sys.stdout = f  # Redirige toda la salida print al archivo
    # Aqui acaba
    production_list[:] = user_productions

    primerosysiguientes.main(production_list)

    print("\tFIRST AND FOLLOW OF NON-TERMINALS")
    for nt in ntl:
        primerosysiguientes.compute_first(nt)
        primerosysiguientes.compute_follow(nt)
        first = sorted(primerosysiguientes.get_first(nt))
        follow = sorted(primerosysiguientes.get_follow(nt))
        print(nt)
        print("\tFirst:\t", primerosysiguientes.get_first(nt))
        print("\tFollow:\t", primerosysiguientes.get_follow(nt), "\n")

    augment_grammar()

    nt_list = list(ntl.keys())
    t_list = list(tl.keys()) + ['$']

    print(nt_list)
    print(t_list, "\n")

    j = calc_states()

    #CON ESTE EXPORTAMOS EN PDF
    #export_items_to_pdf(j, codigos_equivalentes, filename="items_clr1.pdf")

    ctr = 0
    for idx, state in enumerate(j):
        print(f"Item{idx}{{")  # ACA SER CAMBIA EL ITEM POR I SI QUIERES
        pretty_print_items(state, codigos_equivalentes)
        print("}\n")

    table = make_table(j)

    print("\n\tCLR(1) TABLE\n")

    sr, rr = 0, 0

    for i, fila in table.items():
        print(i, "\t", fila)
        shift_count, reduce_count = 0, 0

        for simbolo, acciones in fila.items():
            if acciones == 'Aceptar':
                continue
            if isinstance(acciones, set) and len(acciones) > 1:
                acciones_list = list(acciones)

                tipos = {'shift': 0, 'reduce': 0}
                for accion in acciones_list:
                    if accion.startswith('d'):
                        tipos['shift'] += 1
                    elif accion.startswith('r'):
                        tipos['reduce'] += 1

                # Mostrar nombre del símbolo si existe en el diccionario
                simbolo_legible = codigos_equivalentes.get(simbolo, simbolo)

                if tipos['shift'] > 0 and tipos['reduce'] > 0:
                    sr += 1
                    print(f"⚠️ SR conflict en estado {i}, símbolo '{simbolo_legible}' => acciones: {acciones_list}")
                elif tipos['reduce'] > 1:
                    rr += 1
                    print(f"⚠️ RR conflict en estado {i}, símbolo '{simbolo_legible}' => acciones: {acciones_list}")

    print("\n", sr, "s/r conflicts |", rr, "r/r conflicts")
    #export_table_as_csv_format(table)

    # EXPORTAR TABLA COMO .CSV
    #export_clr1_table_full_csv(table, "tabla_clr1_completa.csv")

    # EXPORTAR SALIDA COMO .TXT
    #sys.stdout = original_stdout  # Restaurar salida estándar
    #print("✅ Archivo 'salida_clr1.txt' generado correctamente.")
    return

def export_table_as_csv_format(table):
    print("estado,símbolo,acción")  # Encabezado CSV
    for estado, fila in table.items():
        for simbolo, accion in fila.items():
            # Buscar si el símbolo tiene código equivalente
            simbolo_codificado = simbolo
            for cod, nombre in codigos_equivalentes.items():
                if nombre == simbolo:
                    simbolo_codificado = cod
                    break

            # Imprimir cada acción, incluso si hay múltiples (conflictos)
            if isinstance(accion, set):
                for a in accion:
                    print(f"{estado},{simbolo_codificado},{a}")
            else:
                print(f"{estado},{simbolo_codificado},{accion}")

import csv

def export_clr1_table_full_csv(table, filename="tabla_clr1_completa.csv"):
    # 1. Obtener todos los símbolos legibles posibles para usar como encabezados
    all_symbols = set()
    for fila in table.values():
        all_symbols.update(fila.keys())

    # Convertir a símbolos legibles
    encabezado = ["estado"] + [codigos_equivalentes.get(s, s) for s in sorted(all_symbols)]

    # 2. Escribir CSV
    with open(filename, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(encabezado)

        for estado, fila in table.items():
            fila_csv = [estado]
            for simbolo in sorted(all_symbols):
                accion = fila.get(simbolo, "")
                if isinstance(accion, set):
                    accion_str = '|'.join(sorted(accion))
                else:
                    accion_str = accion
                fila_csv.append(accion_str)
            writer.writerow(fila_csv)

    print(f"✅ Tabla CLR(1) exportada como CSV en: {filename}")

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import textwrap

def export_lr0_items_to_pdf(states, filename="states_lr0.pdf", show_lambda=False, empty_symbol='λ'):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    margin = inch
    y = height - margin
    c.setFont("Times-Roman", 12)

    for idx, state in enumerate(states):
        titulo = f"Item{idx}{{"
        
        # Page break check
        if y < margin:
             c.showPage()
             c.setFont("Times-Roman", 12)
             y = height - margin
             
        c.drawString(margin, y, titulo)
        y -= 16

        for item in state:
             head, body = item.split('→')
             
             # Sanitize
             for bad_sym in ['λ', 'ε']:
                 body = body.replace(bad_sym, "")
             
             # Handle dot (use '.' for PDF compatibility if font issues, or unicode if supported)
             # User said "correctamente", often means unicode fails. Safest checks:
             # Try simple chars first, or use Helvetica
             
             # Using simple chars for maximum PDF compatibility unless we load a font
             # But user wants "premium". Let's try sticking to text but clean.
             # Arrow -> "->"
             # Dot -> "." or "*" or "(*)" 
             # Let's try to align with GUI but use PDF safe chars if no font.
             # Standard fonts (Times-Roman) supports basic ASCII. 
             # Let's use "->" and "." to be SAFE.
             
             body_display = body.replace('.', '.') # Just keeping dot as dot? or maybe '*'
             # Actually, the user code `item.replace(".", "●")` implies they WANT the blob.
             # But standard PDF font won't show it.
             # I will use a simple dot '.' or a specific char code if known.
             # Better: Use " . " (spaces) to make it visible.
             
             body_display = body_display.strip()
             body_display = " ".join(body_display.split())
             
             if body_display.replace('.', '').strip() == "":
                 if show_lambda:
                     if body_display.startswith('.'):
                          body_display = f". {empty_symbol}" 
                     else:
                          body_display = f"{empty_symbol} ."

             line = f"[ {head} -> {body_display} ]"

             wrapped_lines = textwrap.wrap(line, width=90)
             for wrapped_line in wrapped_lines:
                 if y < margin:
                     c.showPage()
                     c.setFont("Times-Roman", 12)
                     y = height - margin
                 c.drawString(margin, y, wrapped_line)
                 y -= 14
        
        # Closing brace
        if y < margin:
            c.showPage()
            c.setFont("Times-Roman", 12)
            y = height - margin
        c.drawString(margin, y, "}")
        y -= 20

    c.save()
    print(f"✅ PDF generado: {filename}")


if __name__ == "__main__":
    main()
