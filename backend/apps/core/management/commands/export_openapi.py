"""Write the API's OpenAPI schema for the frontend's generated types (`pnpm api:types`)."""

import json
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import translation


class Command(BaseCommand):
    help = "Write the OpenAPI schema of the API as JSON."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("output", type=Path, help="File to write, e.g. ../frontend/openapi.json.")

    def handle(self, *args: Any, output: Path, **options: Any) -> None:
        from config.api import api

        # Titles and descriptions are translatable; the schema file stays in English
        # whatever the environment's language, so it only changes with the API.
        with translation.override("en"):
            schema = api.get_openapi_schema()
            # DjangoJSONEncoder turns lazy translations into text.
            text = json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False, cls=DjangoJSONEncoder)
        output.write_text(text + "\n", encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {output}"))
