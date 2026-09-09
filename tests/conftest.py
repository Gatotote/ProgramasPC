import pytest

# KDF ligero para que los tests no tarden segundos en cada Argon2id.
LIGHT_KDF = {"type": "argon2id", "time_cost": 1, "memory_cost": 8192, "parallelism": 1}


@pytest.fixture
def light_kdf():
    return LIGHT_KDF
