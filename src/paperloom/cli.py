import typer, os
from .pipeline import extract_pdfs

app = typer.Typer(help="Paperloom Extractor (M5.1)")

@app.command()
def extract(
    input: str = typer.Option("data/inputs", help="Folder with PDFs"),
    output: str = typer.Option("data/outputs", help="Folder for outputs"),
    json_name: str = typer.Option("znr_dataset.json"),
    csv_name: str = typer.Option("znr_dataset.csv"),
    excel_name: str = typer.Option("znr_dataset.xlsx"),
    log_level: str = typer.Option("INFO", help="DEBUG|INFO|WARNING|ERROR|CRITICAL"),
):
    """Extract ZnO features from PDFs and export JSON, CSV, and Excel (multi-sheet)."""
    if not os.path.exists(input):
        raise typer.BadParameter(f"Input directory not found: {input}")
    os.makedirs(output, exist_ok=True)
    extract_pdfs(input, output,
                 json_name=json_name, csv_name=csv_name, excel_name=excel_name,
                 log_level=log_level)
    typer.echo(f"Wrote JSON, CSV, and Excel to {output}")

def main():
    app()

if __name__ == "__main__":
    main()
