import typer

app = typer.Typer()


@app.command()
def main():
    """
    Foxops for MegOps, or something.
    """
    print("🦊")


if __name__ == "__main__":
    app()
