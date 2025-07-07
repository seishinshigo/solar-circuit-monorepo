import pytest
from typer.testing import CliRunner

@pytest.fixture(scope="module")
def runner():
    return CliRunner()