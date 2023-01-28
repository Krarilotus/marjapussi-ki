class Functor:
    def __init__(self, name, arity):
        self.name = name
        self.arity = arity

    def __call__(self, *args):
        if len(args) != self.arity:
            raise ValueError(f"Functor {self.name}/{self.arity} called with {len(args)} arguments")
        return f"{self.name}({', '.join(map(str, args))})"
