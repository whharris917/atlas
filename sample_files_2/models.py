"""
A simple module to define data models for testing complex method chains.
"""

class ServiceC:
    """The third object in the chain, with the final method."""
    def d(self) -> str:
        """The final method in the self.a.b().c().d() chain."""
        return "Method D was called."

class ServiceB:
    """The second object in the chain."""
    def __init__(self):
        self._service_c = ServiceC()

    def c(self) -> ServiceC:
        """Returns the object that has method d()."""
        print("Method C was called, returning ServiceC instance.")
        return self._service_c

class ServiceA:
    """The first object in the chain, stored as attribute 'a'."""
    def __init__(self):
        self._service_b = ServiceB()

    def b(self) -> ServiceB:
        """Returns the object that has method c()."""
        print("Method B was called, returning ServiceB instance.")
        return self._service_b
