import asyncio
import click


async def check_port(ip, port, loop):
    conn = asyncio.open_connection(ip, port, loop=loop)
    try:
        reader, writer = await asyncio.wait_for(conn, timeout=0.3)
        print(ip, port, "ok")
        return (ip, port, True)
    except:
        print(ip, port, "nok")
        return (ip, port, False)
    finally:
        if "writer" in locals():
            writer.close()


async def check_port_sem(sem, ip, port, loop):
    async with sem:
        return await check_port(ip, port, loop)


async def run(host, ports, loop):
    # Change this value for concurrency limitation
    sem = asyncio.Semaphore(400)
    tasks = [
        asyncio.ensure_future(check_port_sem(sem, d, p, loop))
        for d in host
        for p in ports
    ]
    responses = await asyncio.gather(*tasks)
    return responses


@click.command()
@click.option(
    "--host", "-h", "host", required=True,
    help="example --ports google.com"
)
@click.option(
    "--ports", "-p", "ports",
    help="example --host 1-100, default=1-65535",
)
def interface(host, ports="1-65535"):
    """Simple CLI"""
    start_port, end_port = ports.split("-")
    return main(host, int(start_port), int(end_port))


def main(host, start_port, end_port):
    host = [host]  # destinations
    ports = [i for i in range(start_port, end_port)]  # ports
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(host, ports, loop))
    loop.run_until_complete(future)
    print("#" * 50)
    print("Results: ", future.result())


if __name__ == "__main__":
    interface()
    main()
