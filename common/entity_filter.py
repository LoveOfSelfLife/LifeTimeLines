
class Filter:
    def __init__(self, attr, value, op="eq"):
        self.attr = attr
        self.value = value
        self.op = op

    def __str__(self):
        return f"{self.attr} {self.op} @{self.attr}"
    
def create_filter_and_params(filters):
    """
    """
    return " and ".join([str(f) for f in filters]).strip(), {f.attr: f.value for f in filters}
    
    