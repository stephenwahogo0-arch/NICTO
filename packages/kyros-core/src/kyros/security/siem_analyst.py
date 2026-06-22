import os
from uuid import uuid4


class SIEMAnalyst:
    def __init__(self):
        self.analyst_id = str(uuid4())[:12]

    async def ingest_logs(self, source: str, file_list: list[str]) -> dict:
        total_lines = 0
        for fp in file_list:
            if os.path.exists(fp):
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        total_lines += len(f.readlines())
                except Exception:
                    pass
        return {"success": True, "source": source, "total_lines_ingested": total_lines, "files_processed": len(file_list), "analyst_id": self.analyst_id}
