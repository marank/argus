"""Supervisor event listener: terminate supervisord when a program enters FATAL."""

import os
import signal
import sys


def main() -> None:
    while True:
        sys.stdout.write("READY\n")
        sys.stdout.flush()
        header = dict(token.split(":") for token in sys.stdin.readline().split())
        payload = sys.stdin.read(int(header["len"]))
        sys.stderr.write(f"Program entered FATAL state, stopping container: {payload}\n")
        sys.stderr.flush()
        os.kill(os.getppid(), signal.SIGTERM)
        sys.stdout.write("RESULT 2\nOK")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
