
import sys
import io
import csv
import importlib.util
from collections import OrderedDict
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QLabel, QLineEdit, 
                             QPlainTextEdit, QPushButton, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSplitter, QFrame, QMessageBox, QListWidget, QCheckBox, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

# --- Dynamic Import for "Generador CLR.py" ---
# Because the filename has spaces, we can't do a normal import.
spec = importlib.util.spec_from_file_location("generador_clr", "Generador CLR.py")
generador_clr = importlib.util.module_from_spec(spec)
sys.modules["generador_clr"] = generador_clr
spec.loader.exec_module(generador_clr)

# Import generator_lr for LR(0)
spec_lr = importlib.util.spec_from_file_location("generator_lr", "generator_lr.py")
generator_lr = importlib.util.module_from_spec(spec_lr)
sys.modules["generator_lr"] = generator_lr
spec_lr.loader.exec_module(generator_lr)

# Import primerosysiguientes (dependency of Generador CLR)
import primerosysiguientes
import generator_ll

class GrammarInputPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Grammar Definition")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addWidget(QLabel("Non-Terminals (separated by |):"))
        self.nt_input = QLineEdit()
        self.nt_input.setPlaceholderText("Ej: S|A|A'|B")
        layout.addWidget(self.nt_input)

        layout.addWidget(QLabel("Terminals (separated by |):"))
        self.t_input = QLineEdit()
        self.t_input.setPlaceholderText("Ej: a|b|id|+|*")
        layout.addWidget(self.t_input)
        
        # Checkboxes for implicit terminals
        self.chk_layout = QHBoxLayout()
        self.chk_lambda = QCheckBox("Add Lambda (λ)")
        self.chk_epsilon = QCheckBox("Add Epsilon (ε)")
        self.chk_layout.addWidget(QLabel("Implicit Terminals:"))
        self.chk_layout.addWidget(self.chk_lambda)
        self.chk_layout.addWidget(self.chk_epsilon)
        layout.addLayout(self.chk_layout)

        layout.addWidget(QLabel("Rules:"))
        
        instructions = QLabel("• One rule per line\n• Use '->' or '→' as separator\n• Tokens separated by space\n• Example: S -> A b")
        instructions.setStyleSheet("color: gray; font-style: italic; margin-left: 10px;")
        layout.addWidget(instructions)
        
        self.productions_input = QPlainTextEdit()
        self.productions_input.setFont(QFont("Courier New", 10))
        self.productions_input.setPlaceholderText("S -> A' b\nA' -> A A'\nA -> id A \nA -> b")
        layout.addWidget(self.productions_input)

        self.build_button = QPushButton("Build Parser")
        self.build_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(self.build_button)
        
        self.setLayout(layout)

class ResultsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Output Panel")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        self.tabs = QTabWidget()
        
        self.table_widget = QTableWidget()
        self.tabs.addTab(self.table_widget, "Parsing Table")
        
        self.first_follow_table = QTableWidget()
        self.tabs.addTab(self.first_follow_table, "First & Follow")
        
        self.tree_widget = QWidget() # Placeholder for Tree
        self.tree_layout = QVBoxLayout(self.tree_widget)
        self.tree_input = QLineEdit()
        self.tree_input.setPlaceholderText("Enter input string (space separated tokens, e.g., 'id + id')")
        self.parse_btn = QPushButton("Parse Input")
        self.tree_output = QPlainTextEdit()
        self.tree_output.setFont(QFont("Courier New", 10))
        
        self.tree_layout.addWidget(QLabel("Input String:"))
        self.tree_layout.addWidget(self.tree_input)
        
        self.parse_btn.setText("Enter Input")
        self.parse_btn.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; padding: 5px;")
        self.tree_layout.addWidget(self.parse_btn)
        
        # New Table for Parsing Steps
        self.parse_steps_table = QTableWidget()
        self.parse_steps_table.setColumnCount(3)
        self.parse_steps_table.setHorizontalHeaderLabels(["Stack", "Input Buffer", "Action"])
        self.parse_steps_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tree_layout.addWidget(self.parse_steps_table)
        
        # self.tree_output = QPlainTextEdit() # Removed text output
        # self.tree_layout.addWidget(self.tree_output)
        
        self.tabs.addTab(self.tree_widget, "Parse Tree")

        self.states_text = QPlainTextEdit()
        self.states_text.setReadOnly(True)
        self.states_text.setFont(QFont("Consolas", 10))
        self.tabs.addTab(self.states_text, "States")
        
        # Checkbox for LR(0) visual preference
        self.chk_show_lambda = QCheckBox("Show λ / ε in States")
        self.chk_show_lambda.setChecked(True) # Default to true as user asked for it
        # Align it right or left?
        layout.addWidget(self.chk_show_lambda)
        
        layout.addWidget(self.tabs)

        self.export_csv_button = QPushButton("Export CSV")
        self.export_csv_button.setStyleSheet("background-color: #009688; color: white; padding: 8px;")
        layout.addWidget(self.export_csv_button)

        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parser Generator - LL/CLR")
        self.resize(1300, 850)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # --- Left Area ---
        input_splitter = QSplitter(Qt.Orientation.Vertical)
        input_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #B0B0B0;
                height: 1px;
            }
        """)
        
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        
        algo_layout = QHBoxLayout()
        algo_layout.addWidget(QLabel("Algorithm:"))
        self.algo_selector = QComboBox()
        self.algo_selector.addItems(["LL(1)", "LR(0)", "SLR(1)", "LALR(1)", "CLR(1)"])
        self.algo_selector.setCurrentText("LL(1)")
        algo_layout.addWidget(self.algo_selector)
        algo_layout.addStretch()
        top_layout.addLayout(algo_layout)
        
        self.grammar_panel = GrammarInputPanel()
        top_layout.addWidget(self.grammar_panel)
        input_splitter.addWidget(top_container)

        # --- Intermediate Results ---
        intermediate_group = QWidget()
        intermediate_layout = QVBoxLayout(intermediate_group)
        intermediate_layout.addWidget(QLabel("Intermediate Results"))
        
        self.intermediate_tabs = QTabWidget()
        self.closure_text = QPlainTextEdit()
        self.closure_text.setReadOnly(True)
        self.closure_text.setFont(QFont("Consolas", 10))
        self.intermediate_tabs.addTab(self.closure_text, "Canonical Collection / Closure")
        
        self.first_follow_text = QPlainTextEdit()
        self.first_follow_text.setReadOnly(True)
        self.first_follow_text.setFont(QFont("Consolas", 10))
        # self.intermediate_tabs.addTab(self.first_follow_text, "First & Follow") # Moved to Output
        
        self.productions_list = QListWidget()
        self.intermediate_tabs.addTab(self.productions_list, "Numbered Rules") # Moved from Output
        
        intermediate_layout.addWidget(self.intermediate_tabs)

        self.states_text = QPlainTextEdit()
        self.states_text.setReadOnly(True)
        self.states_text.setFont(QFont("Consolas", 10))
        # We will add it to the ResultsPanel tabs instead of intermediate, as per plan or requested?
        # User said: "en las tabs de la derecha habrá un cambio ya que es ahora lr0, las tabas serán otras que se usaran, comenzemos con mostrando los estados"
        # So it should be in the right panel (ResultsPanel).

        input_splitter.addWidget(intermediate_group)

        # --- Right Area ---
        self.results_panel = ResultsPanel()

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #B0B0B0;
                width: 1px;
            }
        """)
        main_splitter.addWidget(input_splitter)
        main_splitter.addWidget(self.results_panel)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(main_splitter)

        # Connections
        self.grammar_panel.build_button.clicked.connect(self.build_parser)
        self.results_panel.export_csv_button.clicked.connect(self.export_csv)
        self.results_panel.parse_btn.clicked.connect(self.parse_input_string)
        self.algo_selector.currentTextChanged.connect(self.on_algo_changed) # New Connection
        self.results_panel.tabs.currentChanged.connect(lambda: self.update_export_button_text())
        self.results_panel.chk_show_lambda.stateChanged.connect(self.refresh_lr0_states)

        # State storage
        self.current_table = None
        self.current_states = None
        
        # Initial Visibility Update
        self.on_algo_changed(self.algo_selector.currentText())

    def on_algo_changed(self, algo):
        if algo == "LL(1)":
             self.intermediate_tabs.setTabVisible(0, False) # Closure Hidden
             self.intermediate_tabs.setTabVisible(1, True) # Rules Visible
             
             self.results_panel.tabs.setTabVisible(0, True) # Table Visible
             self.results_panel.tabs.setTabVisible(1, True) # First/Follow Visible
             self.results_panel.tabs.setTabVisible(2, True) # Tree/Steps Visible
             self.results_panel.tabs.setTabVisible(3, False) # States Hidden
             self.results_panel.chk_show_lambda.setVisible(False) # Checkbox Hidden
        elif algo == "LR(0)":
             self.intermediate_tabs.setTabVisible(0, False) # Closure Hidden (using States tab instead)
             self.intermediate_tabs.setTabVisible(1, True) # Rules Visible
             
             self.results_panel.tabs.setTabVisible(0, False) # Table Hidden
             self.results_panel.tabs.setTabVisible(1, False) # First/Follow Hidden
             self.results_panel.tabs.setTabVisible(2, False) # Tree Hidden
             self.results_panel.tabs.setTabVisible(3, True) # States Visible
             self.results_panel.chk_show_lambda.setVisible(True) # Checkbox Visible
        else: # Other algorithms (CLR, etc.)
             self.intermediate_tabs.setTabVisible(0, True) # Closure Visible
             self.intermediate_tabs.setTabVisible(1, True) # Rules Visible
             
             self.results_panel.tabs.setTabVisible(0, True) # Table Visible
             self.results_panel.tabs.setTabVisible(1, True) # First/Follow Visible
             self.results_panel.tabs.setTabVisible(2, False) # Tree Hidden
             self.results_panel.tabs.setTabVisible(3, False) # States Hidden
             self.results_panel.chk_show_lambda.setVisible(False) # Checkbox Hidden
        
        # Update Export Button Text
        self.update_export_button_text()
             
    def update_export_button_text(self):
        # If LR(0) and States tab is active
        if self.algo_selector.currentText() == "LR(0)" and self.results_panel.tabs.currentIndex() == 3:
            self.results_panel.export_csv_button.setText("Export PDF")
        else:
            self.results_panel.export_csv_button.setText("Export CSV")

    def build_parser(self):
        # 1. Input Validation
        nt_text = self.grammar_panel.nt_input.text().strip()
        t_text = self.grammar_panel.t_input.text().strip()
        prod_text = self.grammar_panel.productions_input.toPlainText().strip()

        if not nt_text or not t_text or not prod_text:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        # 2. Reset Backend State
        primerosysiguientes.nt_list.clear()
        primerosysiguientes.t_list.clear()
        primerosysiguientes.production_list.clear()
        # Reset specific module lists if they are separate copies (they seem shared via import)
        generador_clr.nt_list = []
        generator_lr.nt_list = []
        generator_lr.production_list = []
        
        # 3. Parse Inputs
        # Create Objects for NTs
        nt_symbols = [x.strip() for x in nt_text.split('|') if x.strip()]
        for nt in nt_symbols:
            primerosysiguientes.nt_list[nt] = primerosysiguientes.NonTerminal(nt)

        # Create Objects for Terminals
        t_symbols = [x.strip() for x in t_text.split('|') if x.strip()]
        for t in t_symbols:
            primerosysiguientes.t_list[t] = primerosysiguientes.Terminal(t)

        # Add Implicit Terminals
        if self.grammar_panel.chk_lambda.isChecked():
            primerosysiguientes.t_list['λ'] = primerosysiguientes.Terminal('λ')
        if self.grammar_panel.chk_epsilon.isChecked():
            primerosysiguientes.t_list['ε'] = primerosysiguientes.Terminal('ε')

        # Parse Productions

        # Replace '->' with '→' to ensure compatibility with backend (which splits by '→')
        productions = [line.strip().replace('->', '→') for line in prod_text.split('\n') if line.strip()]
        primerosysiguientes.production_list = productions # Assign directly to the list

        # 4. Run Logic & Capture Output
        output_capture = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = output_capture

        try:
            algo = self.algo_selector.currentText()
            
            # --- Common Step: First & Follow ---
            # We always calculate this as it is useful for all (or most)
            # Replicates lines 382-391 in Generador CLR.py logic
            print("--- FIRST & FOLLOW ---\\n")
            first_follow_data = {}
            for nt_name, nt_obj in primerosysiguientes.nt_list.items():
                primerosysiguientes.compute_first(nt_name)
                primerosysiguientes.compute_follow(nt_name)
                
                # Store for table display
                first_follow_data[nt_name] = {
                    "first": primerosysiguientes.get_first(nt_name),
                    "follow": primerosysiguientes.get_follow(nt_name)
                }
                
                print(f"{nt_name}\\n\\tFirst: {first_follow_data[nt_name]['first']}")
                print(f"\\tFollow: {first_follow_data[nt_name]['follow']}\\n")
            
            # Update First & Follow Table
            self.update_first_follow_table(first_follow_data)

            if algo == "LL(1)":
                  # Note: Tabs visibility is handled by on_algo_changed

                  # LL(1) Specific Logic

                 # LL(1) Specific Logic
                 print("--- LL(1) PARSING TABLE ---\\n")
                 table = generator_ll.compute_ll1_table()
                 self.current_table = table
                 self.current_states = None # No format states for LL(1) in the CLR sense

                 display_table = {}
                 for nt, row in table.items():
                     display_table[nt] = {}
                     for term, p_idx in row.items():
          
                         prod = primerosysiguientes.production_list[p_idx]
                         _, body = prod.split("→")
                         display_table[nt][term] = body.strip() # Just the body
                 
                 self.current_table = display_table # Use this for display
                 # Capture nothing else for closure as it doesn't exist
                 self.closure_text.setPlainText("Not applicable for LL(1)")

            elif algo == "CLR(1)":
                # Step B: Augment Grammar
                generador_clr.production_list = primerosysiguientes.production_list
                generador_clr.ntl = primerosysiguientes.nt_list
                generador_clr.tl = primerosysiguientes.t_list
                generador_clr.augment_grammar()
                
                # Update lists in generator module
                generador_clr.nt_list = list(generador_clr.ntl.keys())
                generador_clr.t_list = list(generador_clr.tl.keys()) + ['$']

                # Step C: Calc States (Canonical Collection)
                print("--- CANONICAL COLLECTION (CLOSURE) ---\\n")
                states = generador_clr.calc_states()
                self.current_states = states

                # Print states for the text view
                for idx, state in enumerate(states):
                    print(f"State {idx}:")
                    generador_clr.pretty_print_items(state) # Prints to captured stdout
                    print("")
                
                self.closure_text.setPlainText(output_capture.getvalue())

                # Step D: Make Table
                table = generador_clr.make_table(states)
                self.current_table = table
            elif algo == "LR(0)":
                # Augmented Grammar logic similar to CLR but using generator_lr
                generator_lr.production_list = primerosysiguientes.production_list
                generator_lr.ntl = primerosysiguientes.nt_list
                generator_lr.tl = primerosysiguientes.t_list
                generator_lr.augment_grammar()
                
                # Update visual lists from generator module
                # Note: generator_lr modifies the lists in place provided references are set correctly
                # We need to reflect the augmented production list in the GUI
                
                # UPDATE: Also populate the flat lists required by calc_states
                generator_lr.nt_list = list(generator_lr.ntl.keys())
                generator_lr.t_list = list(generator_lr.tl.keys()) + ['$'] # Add EOF if needed, usually $
                
                # Step C: Calc States
                print("--- LR(0) STATES ---\\n")
                states = generator_lr.calc_states()
                self.current_states = states
                
                # Format output
                show_lambda = self.results_panel.chk_show_lambda.isChecked()
                empty_symbol = 'ε' if self.grammar_panel.chk_epsilon.isChecked() else 'λ'
                formatted_states = generator_lr.format_states_lr0(states, show_lambda=show_lambda, empty_symbol=empty_symbol)
                self.results_panel.states_text.setPlainText(formatted_states)
                
                # Update production list to show augmented rule
                # generator_lr.production_list has the augmented rules now
                primerosysiguientes.production_list = generator_lr.production_list # Sync back for display
                
            else:
                 QMessageBox.information(self, "Info", f"Algorithm {algo} not yet fully implemented in GUI.")
                 return

        except Exception as e:
            sys.stdout = original_stdout
            QMessageBox.critical(self, "Execution Error", f"An error occurred:\\n{str(e)}")
            import traceback
            traceback.print_exc()
            return
        finally:
            sys.stdout = original_stdout

        # 5. Update UI
        # self.first_follow_text.setPlainText(first_follow_str) # Removed text view
        self.update_results_table(self.current_table)
        self.update_productions_list(primerosysiguientes.production_list)
        
        # Adjust tabs visibility based on algo selection (redundant but ensures consistency)
        # self.on_algo_changed(algo) 

        QMessageBox.information(self, "Success", "Parser Generated Successfully.")
        
    def parse_input_string(self):
        if self.algo_selector.currentText() != "LL(1)":
             QMessageBox.warning(self, "Warning", "Parse Tree is currently only for LL(1).")
             return
             
        if not self.current_table:
             QMessageBox.warning(self, "Warning", "Please build the parser first.")
             return
             
        input_str = self.results_panel.tree_input.text().strip()
        if not input_str:
             return
             
        # We need the ACTUAL table with indices
        raw_table = generator_ll.compute_ll1_table()
        start_symbol = list(primerosysiguientes.nt_list.keys())[0]
        
        tokens = input_str.split() # Fix: Define tokens
        result_node, steps = generator_ll.parse_input(raw_table, start_symbol, tokens)
        
        if isinstance(result_node, str):
            # Error in setup or immediate fail (though parse_input returns tuple)
            # If parse_input returns (str, steps)
            QMessageBox.warning(self, "Parse Error", result_node)
            
        # Populate Table
        self.results_panel.parse_steps_table.setRowCount(len(steps))
        for i, step in enumerate(steps):
             self.results_panel.parse_steps_table.setItem(i, 0, QTableWidgetItem(step['stack']))
             self.results_panel.parse_steps_table.setItem(i, 1, QTableWidgetItem(step['input']))
             self.results_panel.parse_steps_table.setItem(i, 2, QTableWidgetItem(step['action']))

    def update_first_follow_table(self, data):
        self.results_panel.first_follow_table.clear()
        if not data:
            return
            
        columns = ["Non-Terminal", "First", "Follow"]
        self.results_panel.first_follow_table.setColumnCount(3)
        self.results_panel.first_follow_table.setHorizontalHeaderLabels(columns)
        self.results_panel.first_follow_table.setRowCount(len(data))
        
        for idx, (nt, sets) in enumerate(data.items()):
            # NT
            self.results_panel.first_follow_table.setItem(idx, 0, QTableWidgetItem(str(nt)))
            
            # First
            first_str = ", ".join(sorted([str(s) for s in sets["first"]]))
            self.results_panel.first_follow_table.setItem(idx, 1, QTableWidgetItem(first_str))
            
            # Follow
            follow_str = ", ".join(sorted([str(s) for s in sets["follow"]]))
            self.results_panel.first_follow_table.setItem(idx, 2, QTableWidgetItem(follow_str))
            
        self.results_panel.first_follow_table.resizeColumnsToContents()
        self.results_panel.first_follow_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)



    def update_results_table(self, table):
        self.results_panel.table_widget.clear()
        
        if not table:
            return

        # Collect columns (all terminals + non-terminals that appear in keys)
        # The table is [State][Symbol] -> Action
        
        all_symbols = set()
        for row in table.values():
            all_symbols.update(row.keys())
        
        # Sort symbols: Terminals first, then Non-Terminals, then $
        # Use existing lists to sort
        sorted_cols = sorted(list(all_symbols)) # Simple sort for now
        
        # Create headers
        self.results_panel.table_widget.setColumnCount(len(sorted_cols))
        self.results_panel.table_widget.setHorizontalHeaderLabels(sorted_cols)
        
        self.results_panel.table_widget.setRowCount(len(table))
        self.results_panel.table_widget.setVerticalHeaderLabels([str(k) for k in table.keys()])

        # Populate
        for r_idx, (state_id, row_data) in enumerate(table.items()):
            for c_idx, symbol in enumerate(sorted_cols):
                if symbol in row_data:
                    action = row_data[symbol]
                    # Format set actions (conflicts) or single strings
                    if isinstance(action, set):
                        text = "/".join(sorted(action))
                        item = QTableWidgetItem(text)
                        item.setBackground(QColor(255, 200, 200)) # Reddish for conflicts
                    else:
                        text = str(action)
                        item = QTableWidgetItem(text)
                        
                        # Color coding
                        if text == "Aceptar":
                            item.setBackground(QColor(200, 255, 200)) # Green
                        elif text.startswith('r'):
                            item.setBackground(QColor(220, 230, 255)) # Light Blue
                    
                    self.results_panel.table_widget.setItem(r_idx, c_idx, item)

        self.results_panel.table_widget.resizeColumnsToContents()

    def update_productions_list(self, prods):
        self.intermediate_tabs.currentWidget().clear() # Since we moved it to intermediate tabs
        # But wait, self.productions_list is a QListWidget, we can access it directly
        self.productions_list.clear() # This was referring to self.results_panel.productions_list in old code
        # Now it is self.productions_list in MainWindow? No, it's inside tabs.
        
        # FIX: The `productions_list` is now in `intermediate_tabs` in MainWindow init for "Intermediate".
        # But we previously defined it in `ResultsPanel`. 
        # In my logic refactor (Step 142), I added `self.productions_list` to `MainWindow`. 
        # I should reference `self.productions_list` directly if I bound it to `self`.
        
        self.productions_list.clear()
        for idx, p in enumerate(prods):
            self.productions_list.addItem(f"{idx}: {p}")

    def export_csv(self):
        # Check if we should do PDF export instead (LR(0) States)
        if self.algo_selector.currentText() == "LR(0)" and self.results_panel.tabs.currentIndex() == 3: # States Tab
             self.export_pdf_lr0()
             return

        # Determine active tab
        current_index = self.results_panel.tabs.currentIndex()
        
        target_table = None
        default_name = "export.csv"
        
        if current_index == 0:
            target_table = self.results_panel.table_widget
            default_name = "parsing_table.csv"
        elif current_index == 1:
            target_table = self.results_panel.first_follow_table
            default_name = "first_follow.csv"
        elif current_index == 2:
            target_table = self.results_panel.parse_steps_table
            default_name = "parse_simulation.csv"
            
        if not target_table or target_table.rowCount() == 0:
            QMessageBox.warning(self, "Warning", "No data to export in the current tab.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", default_name, "CSV Files (*.csv)")
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # Headers
                headers = []
                for i in range(target_table.columnCount()):
                    item = target_table.horizontalHeaderItem(i)
                    headers.append(item.text() if item else f"Column {i}")
                
                # If it's the parsing table, we might want row headers too (Non-Terminals)
                # In QTableWidget, row headers are usually verticalHeaderItems
                if current_index == 0: # Parsing Table
                     # Add a corner header
                     headers.insert(0, "Non-Terminal")
                
                writer.writerow(headers)
                
                # Rows
                for row in range(target_table.rowCount()):
                    row_data = []
                    
                    if current_index == 0: # Parsing Table
                        # Add row header (NT)
                        v_item = target_table.verticalHeaderItem(row)
                        row_data.append(v_item.text() if v_item else f"Row {row}")
                    
                    for col in range(target_table.columnCount()):
                        item = target_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    
                    writer.writerow(row_data)
                    
            QMessageBox.information(self, "Success", f"Data exported to {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV: {str(e)}")

    def refresh_lr0_states(self):
        if self.algo_selector.currentText() == "LR(0)" and self.current_states:
             show_lambda = self.results_panel.chk_show_lambda.isChecked()
             
             # Determine empty symbol based on input checkboxes
             empty_symbol = 'ε' if self.grammar_panel.chk_epsilon.isChecked() else 'λ'
             
             formatted_states = generator_lr.format_states_lr0(self.current_states, show_lambda=show_lambda, empty_symbol=empty_symbol)
             self.results_panel.states_text.setPlainText(formatted_states)

    def export_pdf_lr0(self):
        if not self.current_states:
             QMessageBox.warning(self, "Warning", "No states to export.")
             return
             
        file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "states_lr0.pdf", "PDF Files (*.pdf)")
        if not file_path:
            return
            
        try:
            show_lambda = self.results_panel.chk_show_lambda.isChecked()
            empty_symbol = 'ε' if self.grammar_panel.chk_epsilon.isChecked() else 'λ'
            
            generator_lr.export_lr0_items_to_pdf(
                self.current_states, 
                filename=file_path, 
                show_lambda=show_lambda,
                empty_symbol=empty_symbol
            )
            QMessageBox.information(self, "Success", f"States exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}\n\n(Make sure 'reportlab' is installed)")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
