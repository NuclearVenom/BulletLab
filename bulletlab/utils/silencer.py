"""
Output silencer to suppress PyBullet's C-level stdout/stderr spam.
"""

import os
import sys

class SuppressOutput:
    """A context manager that redirects stdout and stderr to os.devnull
    at both the Python and C/C++ level.
    
    This is necessary because PyBullet uses hardcoded printf/std::cout
    statements (like `b3Warning...` and `b3Printf...`) that bypass Python's
    sys.stdout.
    """
    def __init__(self, suppress: bool = True):
        self.suppress = suppress

    def __enter__(self):
        if not self.suppress:
            return self

        self.null_fds = [os.open(os.devnull, os.O_RDWR) for _ in range(2)]
        self.saved_fds = [os.dup(1), os.dup(2)]

        os.dup2(self.null_fds[0], 1)
        os.dup2(self.null_fds[1], 2)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.suppress:
            return

        os.dup2(self.saved_fds[0], 1)
        os.dup2(self.saved_fds[1], 2)

        for fd in self.null_fds + self.saved_fds:
            os.close(fd)
