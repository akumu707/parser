from enum import Enum


class BasicObjT(Enum):
    Int = 1
    Var = 2
    Bool = 3
    Str = 4


class SimpleObj:

    def __init__(self, t, value):
        self.type = t
        self.value = value

    def __str__(self):
        if self.type == BasicObjT.Bool:
            return "TRUE" if self.value else "FALSE"
        if self.type == BasicObjT.Str:
            return f"\"{self.value}\""
        return str(self.value)

    def eval(self, variable_map):
        if self.type == BasicObjT.Int:
            return int(self.value)
        if self.type == BasicObjT.Bool or self.type == BasicObjT.Str:
            return self.value
        if self.value in variable_map.keys():
            return variable_map[self.value]
        raise Exception("Variable " + self.value + " not assigned")

class OPchain:

    def __init__(self, chain):
        self.chain = chain

    def __str__(self):
        result = f""
        for var, op in self.chain:
            if op is None:
                result+=f"{var}"
            else:
                result+=f"{op}({var})"
        return result

    def eval(self, variable_map):
        result = None
        for var, op in self.chain:
            value = var.eval(variable_map)
            if result is None:
                result = value
            else:
                if op == "+":
                    result += value
                if op == "-":
                    result -= value
                if op == "*":
                    result *= value
                if op == "/":
                    result /= value
        return result


class BinOP:

    def __init__(self, op, l, r):
        self.op = op
        self.left = l
        self.right = r

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

    def eval(self, variable_map):
        left = self.left.eval(variable_map)
        right = self.right.eval(variable_map)
        try:
            if self.op == "-":
                return left+(-right)
            if self.op == "+":
                return left+right
            if self.op == "/":
                return left*(1/right)
            if self.op == "*":
                return left*right
            if self.op == ">":
                return left > right
            if self.op == "<":
                return left < right
            if self.op == "=":
                return left == right
        except TypeError as tperror:
            raise Exception("Type Error: " + str(tperror))


class CommandT(Enum):
    Assign = 1
    Print = 2
    Read = 3
    Do = 4
    If = 5



class Command:

    def __init__(self, t, r, l=None):
        self.type = t
        self.right = r
        self.left = l  # only useful for the jump command

    def __str__(self):
        if self.type == CommandT.Assign:
            return f"{self.left} : {self.right}\n"
        if self.type == CommandT.Print:
            return f"WRITE {self.right}\n"
        if self.type == CommandT.Read:
            return f"READ {self.right}\n"
        if self.type == CommandT.Do:
            return f"DO {self.right}\n"
        result = f"IF {self.left} " + "{\n"
        for command in self.right:
            result += f"\t{command}"
        result +="}\n"
        return result

    def eval(self, variable_map):
        if self.type == CommandT.Assign:
            for char in self.left.value:
                if not ord(char) >= ord("a") and ord(char) <= ord("z"):
                    raise Exception("Variable name is not lowercase")
            variable_map[self.left.value] = self.right.eval(variable_map)
            return variable_map
        if self.type == CommandT.Print:
            if self.right.type == BasicObjT.Var:
                print(self.right.eval(variable_map))
            elif self.right.type == BasicObjT.Int:
                print(self.right.eval(variable_map))
            else:
                raise Exception("Trying to print unprintable object")
            return variable_map
        if self.type == CommandT.Read:
            result = input()
            if result.isdecimal():
                variable_map[self.right.value] = int(result)
                return variable_map
            raise Exception("Trying to assign string to a variable")
        if self.type == CommandT.Do:
            return self.right
        if self.type == CommandT.If:
            if type(self.left.eval(variable_map)) == bool:
                if self.left.eval(variable_map):
                    for command in self.right:
                        command.eval(variable_map)
                return variable_map
            else:
                raise Exception("IF first parameter is not a Bool expression")


class Block:
    def __init__(self, name, commands):
        self.name = name
        self.commands = commands

    def __str__(self):
        result = f"BLOCK {self.name} " + "{\n"
        for command in self.commands:
            result += f"\t{command}"
        return result + "}"

    def eval(self, variable_map):
        for command in self.commands:
            result = command.eval(variable_map)
            if type(result) == dict:
                variable_map = result
            else:
                return result


class Program:
    def __init__(self, parts):
        self.parts = parts
        # dictionary in the form {block_name : Block}

    def __str__(self):
        result = ""
        for part in self.parts.values():
            result += f"{part}\n"
        return result

    def eval(self):
        """Program should start to evaluate the 'main' block and run its commands.
        If there is no 'main' block, throw an error."""
        variable_map = {}
        if "main" in self.parts.keys():
            variable_map["main"] = {}
            result = self.parts["main"].eval(variable_map["main"])
            while result is not None:
                if result in self.parts:
                    variable_map[result] = {}
                    result = self.parts[result].eval(variable_map[result])
                else:
                    raise Exception("No block named "+result+" in code")
        else:
            raise Exception("No 'main' block in code")
