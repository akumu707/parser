from Classes import *
from Lexer import Lexer
import ply.lex as lex
"""

class Parser:

    def __init__(self, code):
        self.nextToken = code[0]
        self.i = 0
        self.programCode = code
        self.codeLen = len(code)

    def Parse(self):
        return self.P()

    def P(self):
        self.programCode = self.programCode.replace(" ", "")
        block_list = self.programCode.split("BLOCK")
        program_dict = {}
        for block in block_list:
            if block:
                args_list = block.split("{")
                parser = Parser(args_list[1][:-1])
                program_dict[args_list[0]] = Block(name=args_list[0],
                                                   commands=parser.B())

        return Program(program_dict)

    def B(self):
        self.programCode = self.programCode.replace(" ", "")
        commands_strings_list = self.programCode.split(";")
        commands_list = []
        for command_string in commands_strings_list:
            parser = Parser(command_string)
            commands_list.append(parser.C())
        return commands_list

    def C(self):
        self.programCode = self.programCode.replace(" ", "")
        self.nextToken = self.programCode[0]
        if not self.nextToken.isupper():
            command_list = self.programCode.split(":=")
            parser = Parser(command_list[0])
            var = parser.F()
            command_list = self.programCode.split(":=")
            parser = Parser(command_list[1])
            exp = parser.E()
            return Command(CommandT.Assign, r=exp, l=var)

        if self.programCode.startswith("GIVE"):
            parser = Parser(self.programCode[4:])
            value = parser.F()
            return Command(CommandT.Print, value)

        if self.programCode.startswith("READ"):
            parser = Parser(self.programCode[4:])
            value = parser.F()
            return Command(CommandT.Read, value)

        if self.programCode.startswith("DO"):
            args = self.programCode[2:]
            args_list = args.split("]")
            parser = Parser(args_list[0][1:])
            be = parser.BE()
            return Command(CommandT.Jmp, l=be, r=args_list[1])

        if self.programCode.startswith("IF"):
            args = self.programCode[2:]
            args_list = args.split("]")
            parser = Parser(args_list[0][1:])
            be = parser.BE()
            parser = Parser(args_list[1][1:-1])
            block = parser.B()
            return Command(CommandT.If, l=be, r=block)

    def BE(self):
        self.programCode = self.programCode.replace(" ", "")
        for i, char in enumerate(self.programCode):
            if char == ">" or char == "<" or char == "=":
                parser = Parser(self.programCode[:i])
                left = parser.E()
                parser = Parser(self.programCode[i + 1:])
                right = parser.E()
                return BinOP(char, l=left, r=right)

    def E(self):
        self.programCode = self.programCode.replace(" ", "")
        for i, char in enumerate(self.programCode[::-1]):
            if char == "+" or char == "-":
                parser = Parser(self.programCode[:len(self.programCode)-i-1])
                left = parser.E()
                parser = Parser(self.programCode[len(self.programCode)-i:])
                right = parser.E()
                return BinOP(char, l=left, r=right)
        parser = Parser(self.programCode)
        return parser.T()

    def T(self):
        self.programCode = self.programCode.replace(" ", "")
        for i, char in enumerate(self.programCode[::-1]):
            if char == "*" or char == "/":
                parser = Parser(self.programCode[:len(self.programCode)-i-1])
                left = parser.T()
                parser = Parser(self.programCode[len(self.programCode)-i:])
                right = parser.T()
                return BinOP(char, l=left, r=right)
        parser = Parser(self.programCode)
        return parser.F()

    def F(self):
        self.programCode = self.programCode.replace(" ", "")
        if self.programCode.isalpha():
            return SimpleObj(BasicObjT.Var, self.programCode)
        return SimpleObj(BasicObjT.Val, int(self.programCode))

# Example:
P = Parser("BLOCK main {READ x; x:= x+6; DO [x > x - 2] other; GIVE x} BLOCK other {y := 9*x + 56; GIVE y} BLOCK otter {DO [x + 3 < 5 *4] other}")
parsed = P.Parse()
print(parsed)
print("-----------------")
parsed.eval()
"""


class Parser:

    def __init__(self, code_file):
        self.code = ""
        with open(code_file) as file:
            for line in file:
                self.code += line
        self.lexer = Lexer()
        self.lexer.build()
        self.tokens = self.lexer.run(self.code)
        self.next_token = 0

    def _raise_exception(self, msg, token):
        line_start = self.code.rfind('\n', 0, token.lexpos) + 1
        raise Exception(f"{msg} on line: {token.lineno}  char: {token.lexpos - line_start}")

    def _accept(self, acc):
        if self.next_token >= len(self.tokens):
            return False
        if self.tokens[self.next_token].value == acc:
            self.next_token += 1
            return True
        return False

    def _expect(self, exp):
        if self.next_token >= len(self.tokens):
            return False
        if self.tokens[self.next_token].value == exp:
            self.next_token += 1
            return True
        self._raise_exception(f"Unexpected char {self.tokens[self.next_token].value}, expected {exp}",
                              self.tokens[self.next_token-1])

    def _get_next_token(self):
        current = self.tokens[self.next_token]
        self.next_token += 1
        return current

    def parse(self):
        program = {}
        while self.next_token < len(self.tokens):
            if self._expect("BLOCK"):
                key = self._get_next_token().value
                block = self._block()
                program[key] = Block(name=key, commands = block)
        return Program(program)

    def _block(self):
        result = []
        if self._expect("{"):
            while not self._accept("}"):
                result.append(self._command())
        return result

    def _command(self):
        if self._accept("WRITE"):
            return Command(CommandT.Print, self._bool_expression())
        if self._accept("READ"):
            return Command(CommandT.Read, self._object())
        if self._accept("IF"):
            return Command(CommandT.If, l=self._bool_expression(), r=self._block())
        if self._accept("DO"):
            return Command(CommandT.Do, r=self._get_next_token().value)
        l = self._object()
        if self._expect(":"):
            r = self._bool_expression()
            return Command(CommandT.Assign, r, l)

    def _bool_expression(self):
        l = self._expression()
        if self._accept(">"):
            r = self._bool_expression()
            if r is None:
                self._raise_exception(f"Expected value after >", self.tokens[self.next_token])
            return BinOP(">", l=l, r=r)
        if self._accept("<"):
            r = self._bool_expression()
            if r is None:
                self._raise_exception(f"Expected value after <", self.tokens[self.next_token])
            return BinOP("<", l=l, r=r)
        if self._accept("="):
            r = self._bool_expression()
            if r is None:
                self._raise_exception(f"Expected value after =", self.tokens[self.next_token])
            return BinOP("=", l=l, r=r)
        return l

    def _expression(self):
        result = []
        op = None
        while True:
            next_char = self._term()
            if next_char is None:
                if op is None:
                    self._raise_exception(f"Expected expression", self.tokens[self.next_token])
                self._raise_exception(f"Expected value after {op}", self.tokens[self.next_token])
            result.append((next_char, op))
            if self._accept("+"):
                op = "+"
            elif self._accept("-"):
                op = "-"
            else:
                if len(result) == 1:
                    return result[0][0]
                return OPchain(result)


    def _term(self):
        result = []
        op = None
        while True:
            next_char = self._object()
            if next_char is None:
                if op is None:
                    self._raise_exception(f"Expected expression", self.tokens[self.next_token])
                self._raise_exception(f"Expected value after {op}", self.tokens[self.next_token])
            result.append((next_char, op))
            if self._accept("/"):
                op = "/"
            elif self._accept("*"):
                op = "*"
            else:
                if len(result) == 1:
                    return result[0][0]
                return OPchain(result)

    def _object(self):
        if self._accept("("):
            exp = self._expression()
            if self._accept(")"):
                return exp
            self._raise_exception(f"Expected )", self.tokens[self.next_token])
        if self.next_token >= len(self.tokens):
            return None
        if self._accept("\""):
            current = ""
            while not self._accept("\""):
                if self.next_token >= len(self.tokens):
                    raise Exception("Missing string indiciator")
                current+=str(self._get_next_token().value)
            return SimpleObj(BasicObjT.Str, current)
        current = self._get_next_token()
        if current.type == "NUMBER":
            return SimpleObj(BasicObjT.Int, current.value)
        if current.type == "TRUE":
            return SimpleObj(BasicObjT.Bool, True)
        if current.type == "FALSE":
            return SimpleObj(BasicObjT.Bool, False)
        if current.value.isalpha():
            return SimpleObj(BasicObjT.Var, current.value)



P = Parser("test.txt")
parsed = P.parse()
print(parsed)
print("-----------------")
parsed.eval()