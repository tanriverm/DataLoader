with open("test_input.sre", "wb") as f:
    for i in range(1024):
        f.write(bytes([i % 256]))
