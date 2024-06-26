from CodeGenError import IllegalOperandException, IllegalRuntimeException
from Utils import *
# from StaticCheck import *
# from StaticError import *
import CodeGenerator as cgen
from MachineCode import JasminCode
from AST import *


class Emitter():
    def __init__(self, filename):
        self.filename = filename
        self.globalVarDirectives = list()
        self.buff = list()
        self.jvm = JasminCode()

    def getJVMType(self, inType):
        typeIn = type(inType)
        if typeIn is NumberType:
            return "F"
        elif typeIn is StringType:
            return "Ljava/lang/String;"
        elif typeIn is cgen.ObjectType:
            return "Ljava/lang/Object;"
        elif typeIn is VoidType:
            return "V"
        elif typeIn is ArrayType:
            return "[" * len(inType.size) + self.getJVMType(inType.eleType)
        elif typeIn is BoolType:
            return "Z"
        elif typeIn is cgen.MType:
            return "(" + "".join(list(map(lambda x: self.getJVMType(x), inType.partype))) + ")" + self.getJVMType(inType.rettype)

    def getFullType(self, inType):
        typeIn = type(inType)
        if typeIn is NumberType:
            return "float"
        elif typeIn is StringType:
            return "java/lang/String"
        elif typeIn is VoidType:
            return "void"

    def emitPUSHICONST(self, in_, frame):
        # in: Int or Sring
        # frame: Frame

        if type(in_) is int:
            frame.push()
            i = in_
            if i >= -1 and i <= 5:
                return self.jvm.emitICONST(i)
            elif i >= -128 and i <= 127:
                return self.jvm.emitBIPUSH(i)
            elif i >= -32768 and i <= 32767:
                return self.jvm.emitSIPUSH(i)
        elif type(in_) is str:
            if in_ == "true":
                return self.emitPUSHICONST(1, frame)
            elif in_ == "false":
                return self.emitPUSHICONST(0, frame)
            else:
                return self.emitPUSHICONST(int(in_), frame)

    def emitPUSHFCONST(self, in_, frame):
        # in_: String
        # frame: Frame

        f = float(in_)
        frame.push()
        rst = str(f)
        if rst == "0.0" or rst == "1.0" or rst == "2.0":
            return self.jvm.emitFCONST(rst)
        else:
            return self.jvm.emitLDC(in_)

    ''' 
    *    generate code to push a constant onto the operand stack.
    *    @param in the lexeme of the constant
    *    @param typ the type of the constant
    '''

    def emitPUSHCONST(self, in_, typ, frame):
        # in_: String typ: Type
        # frame: Frame

        if type(typ) is NumberType:
            return self.emitPUSHFCONST(in_, frame)
        elif type(typ) is StringType:
            frame.push()
            in_ = f'"{in_}"'
            return self.jvm.emitLDC(in_)
        elif type(typ) is BoolType:
            return self.emitPUSHICONST(1 if in_ == "true" else 0, frame)
        else:
            raise IllegalOperandException(in_)

    def emitPUSHBOOLCONST(self, val: bool, frame):
        return self.emitPUSHICONST("1" if val else "0", frame)


    ##############################################################

    def emitALOAD(self, in_, frame):
        # in_: Type
        # frame: Frame
        # ..., arrayref, index -> ..., value

        frame.pop()
        if type(in_) is NumberType:
            return self.jvm.emitFALOAD()
        elif type(in_) is BoolType:
            return self.jvm.emitBALOAD()
        elif type(in_) in [StringType, ArrayType]:
            return self.jvm.emitAALOAD()
        else:
            raise IllegalOperandException(str(in_))

    def emitASTORE(self, in_, frame):
        # in_: Type
        # frame: Frame
        # ..., arrayref, index, value -> ...

        frame.pop()
        frame.pop()
        frame.pop()

        if type(in_) is NumberType:
            return self.jvm.emitFASTORE()
        if type(in_) is BoolType:
            return self.jvm.emitBASTORE()
        elif type(in_) in [StringType, ArrayType]:
            return self.jvm.emitAASTORE()
        else:
            raise IllegalOperandException(str(in_))

    '''    generate the var directive for a local variable.
    *   @param in the index of the local variable.
    *   @param varName the name of the local variable.
    *   @param inType the type of the local variable.
    *   @param fromLabel the starting label of the scope where the variable is active.
    *   @param toLabel the ending label  of the scope where the variable is active.
    '''

    def emitVAR(self, in_, varName, inType, fromLabel, toLabel, frame):
        # in_: Int
        # varName: String
        # inType: Type
        # fromLabel: Int
        # toLabel: Int
        # frame: Frame

        return self.jvm.emitVAR(in_, varName, self.getJVMType(inType), fromLabel, toLabel)

    def emitREADVAR(self, name, inType, index, frame):
        # name: String
        # inType: Type
        # index: Int
        # frame: Frame
        # ... -> ..., value

        frame.push()
        if type(inType) is NumberType:
            return self.jvm.emitFLOAD(index)
        if type(inType) is BoolType:
            return self.jvm.emitILOAD(index)
        elif type(inType) in [StringType, ArrayType]:
            return self.jvm.emitALOAD(index)
        else:
            raise IllegalOperandException(name)

    ''' generate the second instruction for array cell access
    *
    '''

    def emitREADVAR2(self, name, typ, frame):
        # name: String
        # typ: Type
        # frame: Frame
        # ... -> ..., value

        # frame.push()
        raise IllegalOperandException(name)

    '''
    *   generate code to pop a value on top of the operand stack and store it to a block-scoped variable.
    *   @param name the symbol entry of the variable.
    '''

    def emitWRITEVAR(self, name, inType, index, frame):
        # name: String
        # inType: Type
        # index: Int
        # frame: Frame
        # ..., value -> ...

        frame.pop()

        if type(inType) is NumberType:
            return self.jvm.emitFSTORE(index)
        if type(inType) is BoolType:
            return self.jvm.emitISTORE(index)
        elif type(inType) in [StringType, ArrayType]:
            return self.jvm.emitASTORE(index)
        else:
            raise IllegalOperandException(inType)

    ''' generate the second instruction for array cell access
    *
    '''

    def emitWRITEVAR2(self, name, typ, frame):
        # name: String
        # typ: Type
        # frame: Frame
        # ..., value -> ...

        # frame.push()
        raise IllegalOperandException(name)

    ''' generate the field (static) directive for a class mutable or immutable attribute.
    *   @param lexeme the name of the attribute.
    *   @param in the type of the attribute.
    *   @param isFinal true in case of constant; false otherwise
    '''

    def emitATTRIBUTE(self, lexeme, in_, isFinal, value):
        # lexeme: String
        # in_: Type
        # isFinal: Boolean
        # value: String

        return self.jvm.emitSTATICFIELD(lexeme, self.getJVMType(in_), False)

    def emitGETSTATIC(self, lexeme, in_, frame):
        # lexeme: String
        # in_: Type
        # frame: Frame

        frame.push()
        return self.jvm.emitGETSTATIC(lexeme, self.getJVMType(in_))

    def emitPUTSTATIC(self, lexeme, in_, frame):
        # lexeme: String
        # in_: Type
        # frame: Frame

        frame.pop()
        return self.jvm.emitPUTSTATIC(lexeme, self.getJVMType(in_))

    def emitGETFIELD(self, lexeme, in_, frame):
        # lexeme: String
        # in_: Type
        # frame: Frame

        return self.jvm.emitGETFIELD(lexeme, self.getJVMType(in_))

    def emitPUTFIELD(self, lexeme, in_, frame):
        # lexeme: String
        # in_: Type
        # frame: Frame

        frame.pop()
        frame.pop()
        return self.jvm.emitPUTFIELD(lexeme, self.getJVMType(in_))

    ''' generate code to invoke a static method
    *   @param lexeme the qualified name of the method(i.e., class-name/method-name)
    *   @param in the type descriptor of the method.
    '''

    def emitINVOKESTATIC(self, lexeme, in_, frame):
        # lexeme: String
        # in_: Type
        # frame: Frame

        typ = in_
        list(map(lambda x: frame.pop(), typ.partype))
        if not type(typ.rettype) is VoidType:
            frame.push()
        return self.jvm.emitINVOKESTATIC(lexeme, self.getJVMType(in_))

    ''' generate code to invoke a special method
    *   @param lexeme the qualified name of the method(i.e., class-name/method-name)
    *   @param in the type descriptor of the method.
    '''

    def emitINVOKESPECIAL(self, frame, lexeme=None, in_=None):
        # lexeme: String
        # in_: Type
        # frame: Frame

        if not lexeme is None and not in_ is None:
            typ = in_
            list(map(lambda x: frame.pop(), typ.partype))
            frame.pop()
            if not type(typ.rettype) is VoidType:
                frame.push()
            return self.jvm.emitINVOKESPECIAL(lexeme, self.getJVMType(in_))
        elif lexeme is None and in_ is None:
            frame.pop()
            return self.jvm.emitINVOKESPECIAL()

    ''' generate code to invoke a virtual method
    * @param lexeme the qualified name of the method(i.e., class-name/method-name)
    * @param in the type descriptor of the method.
    '''

    def emitINVOKEVIRTUAL(self, lexeme, in_, frame):
        # lexeme: String
        # in_: Type
        # frame: Frame

        typ = in_
        list(map(lambda x: frame.pop(), typ.partype))
        frame.pop()
        if not type(typ) is VoidType:
            frame.push()
        return self.jvm.emitINVOKEVIRTUAL(lexeme, self.getJVMType(in_))

    '''
    *   generate ineg, fneg.
    *   @param in the type of the operands.
    '''

    def emitNEGOP(self, in_, frame):
        # in_: Type
        # frame: Frame
        # ..., value -> ..., result
        return self.jvm.emitFNEG()

    def emitNOT(self, in_, frame):
        # in_: Type
        # frame: Frame

        label1 = frame.getNewLabel()
        label2 = frame.getNewLabel()
        result = list()
        result.append(self.emitIFTRUE(label1, frame))
        result.append(self.emitPUSHCONST("true", in_, frame))
        result.append(self.emitGOTO(label2, frame))
        result.append(self.emitLABEL(label1, frame))
        result.append(self.emitPUSHCONST("false", in_, frame))
        result.append(self.emitLABEL(label2, frame))
        return ''.join(result)

    '''
    *   generate iadd, isub, fadd or fsub.
    *   @param lexeme the lexeme of the operator.
    *   @param in the type of the operands.
    '''

    def emitADDOP(self, lexeme, in_, frame):
        # lexeme: String
        # in_: Type
        # frame: Frame
        # ..., value1, value2 -> ..., result

        frame.pop()
        if lexeme == "+":
            return self.jvm.emitFADD()
        else:
            return self.jvm.emitFSUB()

    '''
    *   generate imul, idiv, fmul or fdiv.
    *   @param lexeme the lexeme of the operator.
    *   @param in the type of the operands.
    '''

    def emitMULOP(self, lexeme, in_, frame):
        # lexeme: String
        # in_: Type
        # frame: Frame
        # ..., value1, value2 -> ..., result

        frame.pop()
        if lexeme == "*":
            return self.jvm.emitFMUL()
        else:
            return self.jvm.emitFDIV()

    def emitDIV(self, frame):
        # frame: Frame

        frame.pop()
        return self.jvm.emitIDIV()

    def emitMOD(self, inType, frame):
        # frame: Frame

        frame.pop()
        return self.jvm.emitFREM()

    '''
    *   generate iand
    '''

    def emitANDOP(self, frame):
        # frame: Frame

        frame.pop()
        return self.jvm.emitIAND()

    '''
    *   generate ior
    '''

    def emitOROP(self, frame):
        # frame: Frame

        frame.pop()
        return self.jvm.emitIOR()

    def emitREOP(self, op, in_, frame): # op: String
        # in_: Type
        # frame: Frame
        # ..., value1, value2 -> ..., result

        result = list()

        labelLoadBool = frame.getNewLabel()
        labelDone = frame.getNewLabel()

        # All of the following instructions: fcmpl, fcmpg, if_acmpeq pop its operands.
        frame.pop()
        frame.pop()

        if op in ['<', '>', '<=', '>=']:
            # a <= b can be converted to not (a > b)
            # a >= b can be converted to not (a < b)
            # fcmpl: load 1 onto the stack if value2 > value1

            result.append(self.jvm.emitFCMPL())
            frame.push()

            # ifge pops the operand.
            result.append(self.jvm.emitIFGT(labelLoadBool) if op in ['>', '<='] else self.jvm.emitIFLT(labelLoadBool))
            frame.pop()

            result.append(self.jvm.emitICONST(1 if op in ['>=', '<='] else 0))
            result.append(self.jvm.emitGOTO(labelDone))
            result.append(self.jvm.emitLABEL(labelLoadBool))
            result.append(self.jvm.emitICONST(1 if op in ['<', '>'] else 0))

            # push the 
            frame.push()
        elif op in ['=', '!=']:
            # fcmpl: load 0 onto the stack if value2 equals to value1.
            # ifeq: jump to the label if the top value on the stack is equal to 0.

            result.append(self.jvm.emitFCMPL())
            frame.push()

            # ifeq pops the operand.
            result.append(self.jvm.emitIFEQ(labelLoadBool))
            frame.pop()

            result.append(self.jvm.emitICONST(1 if op != '=' else 0))
            result.append(self.jvm.emitGOTO(labelDone))
            result.append(self.jvm.emitLABEL(labelLoadBool))
            result.append(self.jvm.emitICONST(1 if op == '=' else 0))

            frame.push()
        elif op in ['==']:
            # if_acmpne: jump to the label if value1 == value2.

            result.append(self.jvm.emitIFACMPEQ(labelLoadBool))
            result.append(self.jvm.emitICONST(0))
            result.append(self.jvm.emitGOTO(labelDone))
            result.append(self.jvm.emitLABEL(labelLoadBool))
            result.append(self.jvm.emitICONST(1))

            frame.push()

        result.append(self.jvm.emitLABEL(labelDone))
        return ''.join(result)

    def emitREJMP(self, op, in_, falseLabel, frame):
        # in_: Type
        # frame: Frame
        # ..., value1, value2 -> ..., result

        result = list()
        frame.pop()
        frame.pop()

        result.append(self.jvm.emitFCMPL())
        frame.push()

        if op == '>':
            result.append(self.jvm.emitIFLE(falseLabel))
        elif op == '<=':
            result.append(self.jvm.emitIFGT(falseLabel))
        elif op == '<':
            result.append(self.jvm.emitIFGE(falseLabel))
        elif op == '>=':
            result.append(self.jvm.emitIFLT(falseLabel))
        if op == '=':
            result.append(self.jvm.emitIFNE(falseLabel))
        elif op == '!=':
            result.append(self.jvm.emitIFEQ(falseLabel))
        elif op == '==':
            result.append(self.jvm.emitIFACMPNE(falseLabel))
        else:
            raise IllegalOperandException(op)

        frame.pop()
        return ''.join(result)

    def emitVARINIT(self, varType, frame):
        if type(varType) is NumberType:
            return self.emitPUSHCONST(0, varType, frame)
        elif type(varType) is BoolType:
            return self.emitPUSHCONST("false", varType, frame)
        elif type(varType) is StringType:
            return self.emitPUSHCONST("", varType, frame)
        elif type(varType) is ArrayType and type(varType.eleType) is StringType:
            return self.emitEMPTYSTRINGARR(varType, frame)
        elif type(varType) is ArrayType:
            code = []
            if len(varType.size) == 1:
                code.append(self.emitNEWARRAY(varType, frame))
            else:
                code += [ self.emitPUSHICONST(int(dim), frame) for dim in varType.size ]
                code.append(self.jvm.emitMULTIANEWARRAY(self.getJVMType(varType), str(len(varType.size))))
            return ''.join(code)
        else:
            raise IllegalOperandException(varType)

    def emitNEWARRAY(self, arrType: ArrayType, frame):
        result = []

        result.append(self.emitPUSHICONST(int(arrType.size[0]), frame))

        if len(arrType.size) == 1:
            if type(arrType.eleType) is NumberType:
                lexeme = "float"
                result.append(self.jvm.emitNEWARRAY(lexeme))
            elif type(arrType.eleType) is BoolType:
                lexeme = "boolean"
                result.append(self.jvm.emitNEWARRAY(lexeme))
            else:
                lexeme = "java/lang/String"
                result.append(self.jvm.emitANEWARRAY(lexeme))
        else:
            subArrType = ArrayType(arrType.size[1:], arrType.eleType)
            result.append(self.jvm.emitANEWARRAY(self.getJVMType(subArrType)))

        frame.pop()
        frame.push()

        return ''.join(result)

    def emitEMPTYSTRINGARR(self, arr_type: ArrayType, frame):
        # stack: ... -> <arr-ref>
        code = []
        code.append(self.emitNEWARRAY(arr_type, frame))

        ele_type = StringType() if len(arr_type.size) == 1 else ArrayType(arr_type.size[1:], StringType()) 

        # store empty strings into the array
        for idx in range(int(arr_type.size[0])):
            code.append(self.emitDUP(frame))
            code.append(self.emitPUSHICONST(int(idx), frame))

            if type(ele_type) is StringType:
                code.append(self.emitPUSHCONST("", ele_type, frame))
            else:
                code.append(self.emitEMPTYSTRINGARR(ele_type, frame))

            code.append(self.emitASTORE(ele_type, frame))

        return ''.join(code)

    '''   generate the method directive for a function.
    *   @param lexeme the qualified name of the method(i.e., class-name/method-name).
    *   @param in the type descriptor of the method.
    *   @param isStatic <code>true</code> if the method is static; <code>false</code> otherwise.
    '''

    def emitMETHOD(self, lexeme, in_, isStatic, frame):
        # lexeme: String
        # in_: Type
        # isStatic: Boolean
        # frame: Frame

        return self.jvm.emitMETHOD(lexeme, self.getJVMType(in_), isStatic)

    '''   generate the end directive for a function.
    '''

    def emitENDMETHOD(self, frame):
        # frame: Frame

        buffer = list()
        buffer.append(self.jvm.emitLIMITSTACK(frame.getMaxOpStackSize()))
        buffer.append(self.jvm.emitLIMITLOCAL(frame.getMaxIndex()))
        buffer.append(self.jvm.emitENDMETHOD())
        return ''.join(buffer)

    def getConst(self, ast):
        # ast: Literal
        if type(ast) is NumberLiteral:
            return (str(ast.value), NumberType())

    '''   generate code to initialize a local array variable.<p>
    *   @param index the index of the local variable.
    *   @param in the type of the local array variable.
    '''

    '''   generate code to initialize local array variables.
    *   @param in the list of symbol entries corresponding to local array variable.    
    '''

    '''   generate code to jump to label if the value on top of operand stack is true.<p>
    *   ifgt label
    *   @param label the label where the execution continues if the value on top of stack is true.
    '''

    def emitIFTRUE(self, label, frame):
        # label: Int
        # frame: Frame

        frame.pop()
        return self.jvm.emitIFGT(label)

    '''
    *   generate code to jump to label if the value on top of operand stack is false.<p>
    *   ifle label
    *   @param label the label where the execution continues if the value on top of stack is false.
    '''

    def emitIFFALSE(self, label, frame):
        # label: Int
        # frame: Frame

        frame.pop()
        return self.jvm.emitIFLE(label)

    def emitIFICMPGT(self, label, frame):
        # label: Int
        # frame: Frame

        frame.pop()
        return self.jvm.emitIFICMPGT(label)

    def emitIFICMPLT(self, label, frame):
        # label: Int
        # frame: Frame

        frame.pop()
        return self.jvm.emitIFICMPLT(label)

    def emitIFFCMPLT(self, trueLabel, falseLabel, frame):
        frame.pop()
        frame.pop()

        cmp = self.jvm.emitFCMPL()
        frame.push()

    '''   generate code to duplicate the value on the top of the operand stack.<p>
    *   Stack:<p>
    *   Before: ...,value1<p>
    *   After:  ...,value1,value1<p>
    '''

    def emitDUP(self, frame):
        # frame: Frame

        frame.push()
        return self.jvm.emitDUP()

    def emitPOP(self, frame):
        # frame: Frame

        frame.pop()
        return self.jvm.emitPOP()

    '''   generate code to exchange an integer on top of stack to a floating-point number.
    '''

    def emitI2F(self, frame):
        # frame: Frame

        return self.jvm.emitI2F()

    def emitF2I(self, frame):
        return self.jvm.emitF2I()

    ''' generate code to return.
    *   <ul>
    *   <li>ireturn if the type is IntegerType or BooleanType
    *   <li>freturn if the type is RealType
    *   <li>return if the type is null
    *   </ul>
    *   @param in the type of the returned expression.
    '''

    def emitRETURN(self, in_, frame):
        # in_: Type
        # frame: Frame

        if type(in_) is NumberType:
            frame.pop()
            return self.jvm.emitFRETURN()
        elif type(in_) is BoolType:
            frame.pop()
            return self.jvm.emitIRETURN()
        elif type(in_) is VoidType:
            return self.jvm.emitRETURN()
        elif type(in_) is ArrayType or type(in_) is StringType:
            frame.pop()
            return self.jvm.emitARETURN()
        else:
            raise IllegalRuntimeException(in_)

    ''' generate code that represents a label	
    *   @param label the label
    *   @return code Label<label>:
    '''

    def emitLABEL(self, label, frame):
        # label: Int
        # frame: Frame

        return self.jvm.emitLABEL(label)

    ''' generate code to jump to a label	
    *   @param label the label
    *   @return code goto Label<label>
    '''

    def emitGOTO(self, label, frame):
        # label: Int
        # frame: Frame

        return self.jvm.emitGOTO(label)

    ''' generate some starting directives for a class.<p>
    *   .source MPC.CLASSNAME.java<p>
    *   .class public MPC.CLASSNAME<p>
    *   .super java/lang/Object<p>
    '''

    def emitPROLOG(self, name, parent):
        # name: String
        # parent: String

        result = list()
        result.append(self.jvm.emitSOURCE(name + ".java"))
        result.append(self.jvm.emitCLASS("public " + name))
        result.append(self.jvm.emitSUPER(
            "java/lang/Object" if parent == "" else parent))
        return ''.join(result)

    def emitLIMITSTACK(self, num):
        # num: Int
        return self.jvm.emitLIMITSTACK(num)

    def emitLIMITLOCAL(self, num):
        # num: Int

        return self.jvm.emitLIMITLOCAL(num)

    def emitEPILOG(self):
        with open(self.filename, "w") as file:
            file.write(''.join(self.buff))

    def emitPROGRAM(self, className, parentClass):
        prolog = self.emitPROLOG(className, parentClass)
        with open(self.filename, "w") as file:
            file.write(prolog + ''.join(self.globalVarDirectives + self.buff))

    ''' print out the code to screen
    *   @param in the code to be printed out
    '''

    def printout(self, in_):
        # in_: String
        self.buff.append(in_)

    def printoutGlobalDirective(self, in_):
        self.globalVarDirectives.append(in_)

    def clearBuff(self):
        self.buff.clear()
