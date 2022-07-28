import asyncio
from asyncio import run as aiorun
from typing import Any, Awaitable, List, Tuple

import typer
from pydantic import AnyUrl

async def run_sequence(*functions: Awaitable[Any]) -> None:
    for function in functions:
        await function


async def run_parallel(*functions: Awaitable[Any]) -> None:
    await asyncio.gather(*functions)


async def check_port(ip: str, port: int, loop: asyncio.AbstractEventLoop) -> Tuple[str, int, bool]:
    conn = asyncio.open_connection(ip, port, loop=loop)
    try:
        _, writer = await asyncio.wait_for(conn, timeout=0.3)  # unpack reader and writer
        print(ip, port, "ok")
        return (ip, port, True)
    except Exception as e:
        print(ip, port, "not ok", e)
        return (ip, port, False)
    finally:
        if "writer" in locals():
            writer.close()


async def check_port_sem(sem: asyncio.Semaphore, ip: str, port: int, loop: asyncio.AbstractEventLoop) -> None:
    async with sem:
        return await check_port(ip, port, loop)


async def run(hosts: List[str], ports: str, loop: asyncio.AbstractEventLoop) -> None:
    # Change this value for concurrency limitation
    sem = asyncio.Semaphore(4000)
    tasks = [
        asyncio.create_task(check_port_sem(sem, host, port, loop))
        for host in hosts
        for port in ports
    ]
    responses = await run_parallel(*tasks)
    return responses


def interface(
    hosts: List[str] = typer.Argument(...), ports: str = typer.Argument(..., help="Ports to check, e.g. '1-65535'")
) -> None:
    # hosts = ['google.com']
    print("Hosts: ", hosts, "Ports: ", ports)
    """Simple CLI"""
    try:
        start_port, end_port = map(int, ports.split("-"))
    except ValueError:
        print("Invalid ports range, try --ports 1-65535")
        raise SystemExit(1)  # exit with error
    return main(hosts, int(start_port), int(end_port))


def main(hosts: List[AnyUrl], start_port: int, end_port: int) -> None:
    async def _main():
        ports = [i for i in range(start_port, end_port)]
        loop = asyncio.get_event_loop()
        await run(hosts, ports, loop)
        print("#" * 50)
    aiorun(_main())


if __name__ == "__main__":
    typer.run(interface)
