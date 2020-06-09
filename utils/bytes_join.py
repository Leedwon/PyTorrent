def join_to_bytes(iterable) -> bytes:
    result = b''
    for element in iterable:
        if type(element) is bytes:
            result = result + element
        else:
            result = result + bytes(element)
    return result
