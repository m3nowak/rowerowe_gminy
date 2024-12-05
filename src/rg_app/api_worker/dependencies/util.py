from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncContextManager, Callable, ContextManager, TypeVar

import fastapi

AppType = TypeVar("AppType", bound=fastapi.FastAPI)


def combined_lifespans_factory(
    *contexts: Callable[[AppType], AsyncContextManager[None]] | Callable[[AppType], ContextManager[None]],
) -> Callable[[AppType], AsyncContextManager[None]]:
    """
    Create a combined lifespan context factory that combines multiple contexts into one!
    """

    @asynccontextmanager
    async def combined_contexts(app: AppType):
        async with AsyncExitStack() as stack:
            for ctx in contexts:
                context_invoked = ctx(app)
                if hasattr(context_invoked, "__aenter__"):
                    assert isinstance(context_invoked, AsyncContextManager)
                    await stack.enter_async_context(context_invoked)
                elif hasattr(context_invoked, "__enter__"):
                    assert isinstance(context_invoked, ContextManager)
                    stack.enter_context(context_invoked)
                else:
                    raise TypeError(f"Unsupported context type: {type(context_invoked)}")
            yield

    return combined_contexts
