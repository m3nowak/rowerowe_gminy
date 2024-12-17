from typing import Annotated

from fast_depends import Depends


def _provide_test_info():
    return "Hello, World!"


TestInfo = Annotated[str, Depends(_provide_test_info)]
