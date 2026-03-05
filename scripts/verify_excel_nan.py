import io
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.excel_utils import parse_center_upload_records, parse_indicator_upload_records


def _to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return buf.getvalue()


def main() -> None:
    center_df = pd.DataFrame(
        [
            {
                "指标名称": "PON装机及时率",
                "支撑中心": "金堂北网络支撑中心",
                "统计日期": "2026-01-13",
                "完成值": 0.8641,
                "基准值": float("nan"),
                "挑战值": float("nan"),
                "得分": float("nan"),
            }
        ]
    )
    center_records, _ = parse_center_upload_records(_to_xlsx_bytes(center_df))
    assert center_records[0]["benchmark"] is None
    assert center_records[0]["challenge"] is None
    assert center_records[0]["score"] is None

    district_df = pd.DataFrame(
        [
            {
                "指标名称": "PON装机及时率",
                "区县": "金堂",
                "统计日期": "2026-01-13",
                "完成值": 0.8641,
                "基准值": float("nan"),
                "挑战值": float("nan"),
                "豁免值": None,
                "零容忍值": None,
                "得分": float("nan"),
            }
        ]
    )
    district_records, _ = parse_indicator_upload_records(_to_xlsx_bytes(district_df))
    assert district_records[0]["benchmark"] is None
    assert district_records[0]["challenge"] is None
    assert district_records[0]["score"] is None

    print("ok")


if __name__ == "__main__":
    main()
