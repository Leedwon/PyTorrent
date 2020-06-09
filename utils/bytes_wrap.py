def wrap(data: bytes, width=20) -> list:
    return [data[i:i + width] for i in range(0, len(data), width)]
