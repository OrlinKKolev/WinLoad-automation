from __future__ import annotations

from pathlib import Path


def export_active_sheet_page1_to_pdf(excel_path: Path, pdf_path: Path) -> None:
    import win32com.client

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False

    wb = None
    try:
        wb = excel.Workbooks.Open(str(excel_path.resolve()))
        ws = wb.ActiveSheet

        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        ws.ExportAsFixedFormat(
            Type=0,
            Filename=str(pdf_path.resolve()),
            Quality=0,
            IncludeDocProperties=True,
            IgnorePrintAreas=False,
            From=1,
            To=1,
            OpenAfterPublish=False,
        )
    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        excel.Quit()