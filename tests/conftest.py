def assert_any_exception(exctype, excinfo):
    assert excinfo.type is exctype
    assert excinfo.value.message == exctype.message
    assert excinfo.value.error_code == exctype.error_code
    assert excinfo.value.status_code == exctype.status_code
