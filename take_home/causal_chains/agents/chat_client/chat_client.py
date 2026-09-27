import click
import httpx


def post_and_read(base_url: str, conversation_id: str, text: str, client: httpx.Client) -> str:
    created = client.post(
        f"{base_url}/conversation/{conversation_id}/messages",
        json={"text": text},
    )
    created.raise_for_status()
    turn_id = created.json()["turn_id"]
    with client.stream(
        "GET",
        f"{base_url}/conversation/{conversation_id}/turn/{turn_id}/sse",
    ) as response:
        response.raise_for_status()
        return response.read().decode()


@click.command()
@click.option("--base-url", default="http://127.0.0.1:8000")
@click.option("--conversation-id", default="1")
@click.option("--text", required=True)
def main(base_url: str, conversation_id: str, text: str) -> None:
    with httpx.Client() as client:
        click.echo(post_and_read(base_url, conversation_id, text, client), nl=False)


if __name__ == "__main__":
    main()
