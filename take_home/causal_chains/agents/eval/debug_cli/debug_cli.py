import click
import httpx


def post_and_read(
    base_url: str,
    conversation_id: str,
    query: str,
    client: httpx.Client,
) -> None:
    created = client.post(
        f"{base_url}/conversation/{conversation_id}/messages",
        json={"text": query},
    )
    created.raise_for_status()
    body = created.json()
    turn_id = body["turn"]["turn_id"]
    with client.stream(
        "GET",
        f"{base_url}/conversation/{conversation_id}/turn/{turn_id}/sse",
        params={
            "include_traces": True,
            "after_message": body["turn"]["from_message"],
        },
    ) as response:
        response.raise_for_status()
        for chunk in response.iter_text():
            click.echo(chunk, nl=False)


@click.command()
@click.option("--base-url", default="http://127.0.0.1:8000")
@click.option("--conversation-id", default="1")
@click.option("--query", required=True)
def main(
    base_url: str,
    conversation_id: str,
    query: str
) -> None:
    with httpx.Client(timeout=httpx.Timeout(300.0)) as client:
        post_and_read(base_url, conversation_id, query, client)


if __name__ == "__main__":
    main()
