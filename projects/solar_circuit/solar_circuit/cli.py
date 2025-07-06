import typer

app = typer.Typer(help="Solar Circuit CLI")
cmd = typer.Typer(help="Subcommands")
app.add_typer(cmd)

@cmd.command("hello")
def hello(
    name: str = typer.Argument("world", help="呼びかける名前")   # ← ここを Argument に
) -> None:
    """動作確認コマンド"""
    typer.echo(f"Hello {name}!")

def main() -> None:
    app()

if __name__ == "__main__":
    main()
