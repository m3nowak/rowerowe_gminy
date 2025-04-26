from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncContextManager, Callable, ContextManager

import faststream


def combined_lifespans_factory(
    *contexts: Callable[[faststream.ContextRepo], AsyncContextManager[None]]
    | Callable[[faststream.ContextRepo], ContextManager[None]],
) -> Callable[[faststream.ContextRepo], AsyncContextManager[None]]:
    """
    Create a combined lifespan context factory that combines multiple contexts into one!
    """

    @asynccontextmanager
    async def combined_contexts(ctx_repo: faststream.ContextRepo):
        async with AsyncExitStack() as stack:
            for ctx in contexts:
                context_invoked = ctx(ctx_repo)
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
