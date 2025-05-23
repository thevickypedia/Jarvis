import re
import os
import pathlib
import socket

import requests


# noinspection HttpUrlsUsage
def construct_enum(
    offline_port: int, offline_host: str = socket.gethostbyname("localhost")
):
    url = f"http://{offline_host}:{offline_port}/openapi.json"
    response = requests.get(url)
    loaded_endpoints = list(sorted(response.json()["paths"].keys(), key=len))
    for endpoint in loaded_endpoints:
        print(f'{str(endpoint).lstrip("/")} = "{endpoint}"')


def gather_routers():
    path = os.path.join(
        pathlib.Path(__file__).parent.parent, "jarvis", "api", "routers"
    )
    for file in os.listdir(path):
        if file.endswith(".py"):
            with open(os.path.join(path, file)) as fstream:
                lines = fstream.readlines()
                for idx, line in enumerate(lines):
                    if "@router" in line:
                        if "/mybad" in line:
                            func_name = re.search(
                                r"(?<=def\s)(\w+)(?=\s*\()", lines[idx + 1]
                            ).group(1)
                            key = file.replace(".py", f".{func_name}")
                            yield {key: line.strip()}
                        else:
                            collection = lines[idx:]
                            grouped, key = [], None
                            for inline in collection:
                                inline = inline.strip()
                                if inline.startswith("async"):
                                    func_name = re.search(
                                        r"(?<=def\s)(\w+)(?=\s*\()", inline
                                    ).group(1)
                                    key = file.replace(".py", f".{func_name}")
                                    break
                                grouped.append(inline)
                            else:
                                raise
                            assert key, "No key found"
                            assert grouped, "Logic for grouping parameters failed"
                            value = (
                                " ".join(grouped)
                                .replace("( ", "(")
                                .replace(" )", ")")
                                .replace(",)", ")")
                            )
                            value = value.replace(
                                "@router.get(",
                                f'APIRoute(endpoint={key}, methods=["GET"], ',
                            )
                            value = value.replace(
                                "@router.post(",
                                f'APIRoute(endpoint={key}, methods=["POST"], ',
                            )
                            value = value.replace(
                                "@router.websocket(",
                                f"APIWebSocketRoute(endpoint={key}, ",
                            )
                            yield value


def codifier():
    enums = {}
    gathered_routers = []
    for router in gather_routers():
        match = re.search(r'path="(.+?)"', router)
        if match:
            match = match.group(1)
            if match == "/":
                enums["/"] = "root"
                router = router.replace(match, "root")
            else:
                enums[match] = match.lstrip("/").replace("-", "_").replace(".", "_")
                router = router.replace(match, enums[match])
            gathered_routers.append(router)
        else:
            enums[router] = router
            gathered_routers.append(router)
    return {
        "sorted_enums": dict(sorted(enums.items(), key=lambda item: len(item[0]))),
        "gathered_routers": gathered_routers,
    }


def construct_routers():
    codified = codifier()
    sorted_enums = codified["sorted_enums"]
    gathered_routers = codified["gathered_routers"]
    for key, value in sorted_enums.items():
        print(f'{value} = "{key}"')

    print("\n\n\n\n")

    for router in gathered_routers:
        print(router)


if __name__ == "__main__":
    construct_routers()
