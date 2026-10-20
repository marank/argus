import logging
import re


class HideJobArguments(logging.Filter):
    """Procrastinate logs each job with its arguments; for mails that is the recipient and the text.

    Turns ``task[42](to='…', body='…')`` into ``task[42](…)``.
    """

    # Greedy: a ")" inside the arguments must not end the match early.
    arguments = re.compile(r"(\[\d+\])\(.*\)", re.DOTALL)

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name.startswith("procrastinate") and isinstance(record.msg, str):
            record.msg = self.arguments.sub(r"\1(…)", record.msg)
        return True
