import pytest

from bovedafacial.crypto import keyslots as K


def test_recovery_phrase_roundtrip():
    phrase = K.generate_recovery_phrase()
    assert len(phrase.split()) == 24
    assert K.phrase_is_valid(phrase)
    assert K.phrase_is_valid(f"  {phrase.upper()}  ")  # se normaliza


def test_pin_slot_roundtrip(light_kdf):
    mk = K.new_master_key()
    slot = K.wrap_pin_slot("correcto-horse", mk, light_kdf)
    assert K.unwrap_pin_slot("correcto-horse", slot, light_kdf) == mk


def test_pin_slot_wrong_pin(light_kdf):
    mk = K.new_master_key()
    slot = K.wrap_pin_slot("123456", mk, light_kdf)
    with pytest.raises(K.WrongSecret):
        K.unwrap_pin_slot("654321", slot, light_kdf)


def test_recovery_slot_roundtrip():
    mk = K.new_master_key()
    phrase = K.generate_recovery_phrase()
    slot = K.wrap_recovery_slot(phrase, mk)
    assert K.unwrap_recovery_slot(phrase, slot) == mk


def test_recovery_slot_wrong_phrase():
    mk = K.new_master_key()
    slot = K.wrap_recovery_slot(K.generate_recovery_phrase(), mk)
    with pytest.raises(K.WrongSecret):
        K.unwrap_recovery_slot(K.generate_recovery_phrase(), slot)


def test_recovery_slot_garbage_phrase():
    mk = K.new_master_key()
    slot = K.wrap_recovery_slot(K.generate_recovery_phrase(), mk)
    with pytest.raises(K.WrongSecret):
        K.unwrap_recovery_slot("esto no es una frase bip39 valida", slot)


def test_wrapped_mk_not_plaintext(light_kdf):
    mk = K.new_master_key()
    slot = K.wrap_pin_slot("123456", mk, light_kdf)
    assert mk not in slot.wrapped_mk
    assert len(slot.wrapped_mk) == K.MK_LEN + 16  # ciphertext + tag GCM
