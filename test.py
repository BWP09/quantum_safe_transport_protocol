headers_input = "key1: value1\nk1: v1"
headers = {}

for line in headers_input.split("\n"):
    k, v = line.split(":", 1)

    headers[k.strip()] = v.strip()

print(headers)