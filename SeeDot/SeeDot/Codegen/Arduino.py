import numpy as np

import IR.IR as IR
import IR.IRUtil as IRUtil

import Type as Type

from Codegen.CodegenBase import CodegenBase

from Util import *

class Arduino(CodegenBase):

	def __init__(self, writer, decls, expts, intvs, cnsts, expTables, VAR_IDF_INIT):
		self.out = writer
		self.decls = decls
		self.expts = expts
		self.intvs = intvs
		self.cnsts = cnsts
		self.expTables = expTables
		self.VAR_IDF_INIT = VAR_IDF_INIT

	# Print the compiled code (IR)
	def printAll(self, prog:IR.Prog, expr:IR.Expr):
		self._out_prefix()
		self.print(prog)
		self._out_suffix(expr)

	def _out_prefix(self):
		if outputPragmas():
			self.printArduinoIncludes()
		else:
			self.printCincludes()

		self.printExpTables()
		
		if outputPragmas():
			self.printArduinoHeader()
		else:
			self.printCHeader()

		self.printVarDecls()

		self.printConstDecls()
		
		self.out.printf('\n')

	def printArduinoIncludes(self):
		self.out.printf('#include <Arduino.h>\n\n', indent=True)
		self.out.printf('#include "config.h"\n', indent=True)
		self.out.printf('#include "predict.h"\n', indent=True)
		self.out.printf('#include "Arduino.h"\n', indent=True)
		self.out.printf('#include "model.h"\n\n', indent=True)
		self.out.printf('using namespace model;\n\n', indent=True)

	def printCincludes(self):
		self.out.printf('#include <iostream>\n\n', indent=True)
		self.out.printf('#include "datatypes.h"\n', indent=True)
		self.out.printf('#include "predictors.h"\n', indent=True)
		self.out.printf('#include "library.h"\n', indent=True)
		self.out.printf('#include "model.h"\n\n', indent=True)
		self.out.printf('using namespace std;\n', indent=True)
		if outputPragmas():
			print('\n', indent=True)
		else:
			self.out.printf('using namespace %s_fixed;\n\n' % (getAlgo()), indent=True)

	def printExpTables(self):
		for exp, [table, [tableVarA, tableVarB]] in self.expTables.items():
			self.printExpTable(table[0], tableVarA)
			self.printExpTable(table[1], tableVarB)
			self.out.printf('\n')

	def printExpTable(self, table_row, var):
		if outputPragmas():
			self.out.printf('const PROGMEM MYINT %s[%d] = {\n' % (var.idf, len(table_row)), indent = True)
		else:
			self.out.printf('const MYINT %s[%d] = {\n' % (var.idf, len(table_row)), indent = True)
		self.out.increaseIndent()
		self.out.printf('', indent = True)
		for i in range(len(table_row)):
			self.out.printf('%d, ' % table_row[i])
		self.out.decreaseIndent()
		self.out.printf('\n};\n')

	def printArduinoHeader(self):
		self.out.printf('int predict() {\n', indent=True)
		self.out.increaseIndent()

	def printCHeader(self):
		self.out.printf('int seedotFixed(MYINT **X) {\n', indent=True)
		self.out.increaseIndent()

	def printVarDecls(self):
		for decl in self.decls:
			if decl in self.VAR_IDF_INIT:
				continue
			typ_str = IR.DataType.getIntStr()
			idf_str = decl
			type = self.decls[decl]
			if Type.isInt(type): shape_str = ''
			elif Type.isTensor(type): shape_str = ''.join(['[' + str(n) + ']' for n in type.shape])
			self.out.printf('%s %s%s;\n', typ_str, idf_str, shape_str, indent=True)
		self.out.printf('\n')

	def printConstDecls(self):
		for cnst in self.cnsts:
			var, num = cnst, self.cnsts[cnst]
			if np.iinfo(np.int16).min <= num <= np.iinfo(np.int16).max:
				self.out.printf('%s = %d;\n', var, num, indent=True)
			elif np.iinfo(np.int32).min <= num <= np.iinfo(np.int32).max:
				self.out.printf('%s = %dL;\n', var, num, indent=True)
			elif np.iinfo(np.int64).min <= num <= np.iinfo(np.int64).max:
				self.out.printf('%s = %dLL;\n', var, num, indent=True)
			else:
				assert False

	def _out_suffix(self, expr:IR.Expr):
		self.out.printf('\n')

		type = self.decls[expr.idf]

		if Type.isInt(type):
			if outputPragmas():
				self.out.printf('return ', indent = True)
			else:
				self.out.printf('return ', indent = True)
			self.print(expr)
			if outputPragmas():
				self.out.printf(';\n')
			else:
				self.out.printf(';\n')
		elif Type.isTensor(type):
			idfr = expr.idf
			exponent = self.expts[expr.idf]
			num = 2 ** exponent

			if type.dim == 0:
				if outputPragmas():
					self.out.printf('Serial.println(', indent = True)
				else:
					self.out.printf('cout << ', indent = True)
				self.out.printf('float(' + idfr + ')*' + str(num))
				if outputPragmas():
					self.out.printf(', 6);\n')
				else:
					self.out.printf(' << endl;\n')
			else:
				iters = []
				for i in range(type.dim):
					s = chr(ord('i') + i)
					tempVar = IR.Var(s)
					iters.append(tempVar)
				expr_1 = IRUtil.addIndex(expr, iters)
				cmds = IRUtil.loop(type.shape, iters, [IR.PrintAsFloat(expr_1, exponent)])
				self.print(IR.Prog(cmds))
		else:
			assert False

		self.out.decreaseIndent()
		self.out.printf('}\n', indent=True)
