# Device Under Test Class

# Pin - physical connection
# Port - Unit functional representationof pin or group of pins
# Cell - BSR cell. Can be associated with Port, but not necessarily

class DUT:
  def __init__(self, ast=None, idcode=None):
    # Create empty placeholders
    self.inner_id = None
    self.idcode = None
    self.name = ''
    self.package = ''

    self.chain_id = None

    self.pins = None
    self.registers = [["BYPASS", 1]]
    self.instructions = []

    if ast is not None:
      self.addAST(ast)
    elif idcode is not None:
      self.idcode = idcode

  def addAST(self, ast):
    self.ast = ast
    
    # Assign name, package and ID
    self.name = ''.join(self.ast["component_name"])
    self.package = self.ast["generic_parameter"]["default_device_package_type"]
    self.idcode = self.getID()

    # Discover regs and instructions
    self.addRegisters()
    self.addInstructions()

    # Create pin dict
    pins = self.ast['device_package_pin_mappings'][0]['pin_map']
    plist = [{'pin_id': pn, 'name': p['port_name']} for p in pins for pn in p['pin_list']]

    # For searching pins by port
    self.port_dict = [p['name'] for p in plist]

    # Save as dict of dicts
    self.pins = dict([(p[0], p[1]) for p in enumerate(plist)])

    # Add port logic
    if self.ast["logical_port_description"] is not None:
      for group_id, gr in enumerate(self.ast["logical_port_description"]):
        for port in gr["identifier_list"]:
          self.setPort(port, "port_group", group_id)
          self.setPort(port, "pin_type", gr['pin_type'])
    
    # Make pins addressable by pin_id
    self.pin_dict = dict([(p[1]['pin_id'], p[0]) for p in enumerate(plist)])


  def setPort(self, port, key, value):
    pid = [i for i, x in self.pins.items() if x['name'] == port] 
    for p in pid:
      self.pins[p][key] = value
  
  def getID(self):
    if "idcode_register" not in self.ast["optional_register_description"]:
      idcode = [''.join(reg["idcode_register"]) for reg in self.ast["optional_register_description"] if "idcode_register" in reg]
    else:
      idcode = [''.join(self.ast["optional_register_description"]["idcode_register"])]
    return idcode[0]

  def addRegisters(self, name=None, length=None):
    # Manually add registers or discover from AST
    if name is not None and length is not None:
      self.registers.append([name, length])
    if self.ast is None: return
    # Read registers from AST

    # Add IR first
    self.registers.append(["IR", int(self.ast["instruction_register_description"]["instruction_length"])])
    
    # And now BSR
    self.registers.append(["BSR", int(self.ast["boundary_scan_register_description"]["fixed_boundary_stmts"]["boundary_length"])])
    
    # "optional_register_description" - description of registers. Can be list of dicts or a dict
    # Pack in list if dict
    if hasattr(self.ast["optional_register_description"], 'keys'):
      reg_desc_ast = [self.ast["optional_register_description"]]
    else:
      reg_desc_ast = self.ast["optional_register_description"]
    instr = []
    for desc in reg_desc_ast:
      reg_keys = [k for k in desc.keys()]
      reg_cont = ''.join(desc[reg_keys[0]])
      inst_len = len(reg_cont)
      inst_name = reg_keys[0].upper().replace('_REGISTER', '')
      # Add register
      instr.append([inst_name, inst_len])
    # "register_access_description" - register names + len + instr
    regs_ast = self.ast["register_access_description"]
    add_regs = []
    for reg in regs_ast:
      reg_name = reg["register"]["reg_name"]
      reg_len = None
      if "reg_length" in reg['register']: reg_len = int(reg["register"]["reg_len"])
      for inst in reg["instruction_capture_list"]:
        # Append reg_len if None and instruction is in instr
        inst_name = inst["instruction_name"]
        if reg_len is None:
          reg_lens = [i for i,x in enumerate(instr) if x[0]==inst_name]
          if len(reg_lens) > 0: 
            # If reg is in instr, then take tength from there
            reg_len = instr[reg_lens[0]][1]
            # Also del the item from instr. I will use remaining not found instr as reg names
            del instr[reg_lens[0]]
        # Append register to self
        if reg_name not in [r[0] for r in self.registers]: self.registers.append([reg_name, reg_len])
        # Append instruction
        if inst_name not in [r[0] for r in self.instructions]: self.instructions.append([inst_name, None, reg_name])
    # Append remaining instr as registers
    for i in instr:
      # Append register to self
      if i[0] not in [r[0] for r in self.registers]: self.registers.append(i)
      # Append instruction
      if i[0] not in [r[0] for r in self.instructions]: self.instructions.append([i[0], None, i[0]])      

  def addInstructions(self, name=None, opcode=None, reg=None):
    # Manually add instructions or discover from AST
    if name is not None and opcode is not None:
      self.instructions.append([name, opcode, reg])
    if self.ast is None: return
    for inst in self.ast["instruction_register_description"]["instruction_opcodes"]:
      reg = None
      # If name is BYPASS, then assign BYPASS register
      if inst["instruction_name"] is None: reg = 'BYPASS'
      # Otherwise use BSR
      if reg is None: reg = "BSR"
      # Append if does not exist
      if inst["instruction_name"] not in [i[0] for i in self.instructions]:
        self.instructions.append([inst["instruction_name"], inst["opcode_list"][0], reg])
      # Update opcode if instruction present and no opcode
      else:
        iid = [i for i,x in enumerate(self.instructions) if x[0] == inst["instruction_name"]][0] 
        if self.instructions[iid][1] is None: self.instructions[iid][1] = inst["opcode_list"][0]

  def prepareBSR(self):
    # TODO: Parse BSR
    pass