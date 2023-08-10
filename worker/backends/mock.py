from .kafkameta import KafkaMeta


class ConsumerMock(KafkaMeta):
    def __init__(self):
        pass

    def run(self) -> None:
        pass
