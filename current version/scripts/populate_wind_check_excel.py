"""Legacy compatibility wrapper. Use app.pipeline.generate_reports instead."""

from app.pipeline.generate_reports import main


if __name__ == "__main__":
    main()