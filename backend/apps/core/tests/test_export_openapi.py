import json

from django.core.management import call_command


def test_writes_the_schema_with_unique_operation_ids(tmp_path):
    output = tmp_path / "openapi.json"

    call_command("export_openapi", output)

    schema = json.loads(output.read_text())
    operation_ids = [op["operationId"] for path in schema["paths"].values() for op in path.values()]
    assert "/api/health" in schema["paths"]
    assert len(operation_ids) == len(set(operation_ids))
