

class Myvalues:
  def __init__(self):
    pass

securedrop_test_vars = Myvalues()

def inject_vars(value):
    res = Myvalues()
    for key, value in value.items():
        setattr(res, key, value)
    return res
