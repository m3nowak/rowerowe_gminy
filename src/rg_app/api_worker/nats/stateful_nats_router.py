from faststream.nats.fastapi import NatsRouter


class StatefulNatsRouter(NatsRouter):
    def attach_state(self, state):
        self.state = state
