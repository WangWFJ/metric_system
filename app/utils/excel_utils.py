import io
from collections import defaultdict

import pandas as pd


def build_template_xlsx(columns: list[str], desc_row: dict, sample_row: dict, sheet_name: str = "模板") -> bytes:
    df = pd.DataFrame([desc_row, sample_row], columns=columns)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()


def parse_indicator_upload_records(contents: bytes) -> tuple[list[dict], int]:
    df = pd.read_excel(io.BytesIO(contents))
    rename_map = {
        "指标名称": "indicator_name",
        "区县": "district_name",
        "统计日期": "stat_date",
        "完成值": "value",
        "基准值": "benchmark",
        "挑战值": "challenge",
        "豁免值": "exemption",
        "零容忍值": "zero_tolerance",
        "得分": "score",
        "类型ID": "type_id",
        "类型名称": "type_name",
    }
    df.rename(columns={c: rename_map.get(str(c).strip(), c) for c in df.columns}, inplace=True)
    required_cols = ["indicator_name", "district_name", "stat_date", "value"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    df["stat_date"] = pd.to_datetime(df["stat_date"], errors="coerce").dt.date
    df = df.where(pd.notna(df), None)
    records = df.to_dict(orient="records")
    return records, len(df)


def parse_center_upload_records(contents: bytes) -> tuple[list[dict], int]:
    df = pd.read_excel(io.BytesIO(contents))
    rename_map = {
        "指标名称": "indicator_name",
        "支撑中心": "center_name",
        "统计日期": "stat_date",
        "完成值": "value",
        "基准值": "benchmark",
        "挑战值": "challenge",
        "得分": "score",
        "类型ID": "type_id",
        "类型名称": "type_name",
    }
    df.rename(columns={c: rename_map.get(str(c).strip(), c) for c in df.columns}, inplace=True)
    required_cols = ["indicator_name", "center_name", "stat_date", "value"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    df["stat_date"] = pd.to_datetime(df["stat_date"], errors="coerce").dt.date
    df = df.where(pd.notna(df), None)
    records = df.to_dict(orient="records")
    return records, len(df)


def parse_indicator_manage_upload_records(contents: bytes) -> tuple[list[dict], int]:
    df = pd.read_excel(io.BytesIO(contents))
    rename_map = {
        "指标名称": "indicator_name",
        "单位": "unit",
        "专业中文名": "major_name",
        "类型中文名": "type_name",
        "是否正向": "is_positive",
        "状态": "status",
        "版本": "version",
        "说明": "description",
        "专业ID": "major_id",
        "类型ID": "type_id",
    }
    df.rename(columns={c: rename_map.get(str(c).strip(), c) for c in df.columns}, inplace=True)
    if "indicator_name" not in df.columns:
        raise ValueError("Missing required column: indicator_name")
    df = df.where(pd.notna(df), None)
    records = df.to_dict(orient="records")
    return records, len(df)


def build_export_xlsx(rows: list[dict], columns_rename: dict[str, str], sheet_name: str = "导出") -> bytes:
    if not rows:
        rows = [{"_": ""}]
    df = pd.DataFrame(rows)
    df = df.rename(columns=columns_rename)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()


def build_center_pivot_xlsx(rows: list[dict]) -> bytes:
    if not rows:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame({"提示": ["无数据"]}).to_excel(writer, index=False, sheet_name="空")
        return buf.getvalue()

    ordered_ind_ids: list[int] = []
    name_map: dict[int, str] = {}
    pos_map: dict[int, int] = {}
    seen = set()
    for r in rows:
        iid = int(r.get("indicator_id"))
        if iid not in seen:
            ordered_ind_ids.append(iid)
            seen.add(iid)
        name_map[iid] = str(r.get("indicator_name") or f"指标{iid}")
        pos_map[iid] = int(r.get("is_positive") if r.get("is_positive") is not None else 1)

    group_by_date: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        group_by_date[str(r.get("stat_date"))].append(r)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for stat_date, date_rows in sorted(group_by_date.items()):
            agg: dict[int, dict[int, dict[str, float | None]]] = defaultdict(dict)
            extra_cols: dict[int, tuple[str, str]] = {}
            for r in date_rows:
                cid = int(r.get("center_id"))
                iid = int(r.get("indicator_id"))
                val = r.get("value")
                sc = r.get("score")
                agg[cid][iid] = {
                    "value": float(val) if val is not None else None,
                    "score": float(sc) if sc is not None else None,
                }
                extra_cols[cid] = (str(r.get("district_name") or ""), str(r.get("center_name") or ""))

            data = []
            for cid, vals in agg.items():
                dname, cname = extra_cols.get(cid, ("", ""))
                row = {"中心ID": cid, "区县": dname, "支撑中心": cname}
                for iid in ordered_ind_ids:
                    col_name = name_map.get(iid, f"指标{iid}")
                    v = vals.get(iid) or {}
                    row[col_name] = v.get("value")
                    row[f"{col_name}-得分"] = v.get("score")
                data.append(row)

            df = pd.DataFrame(data)
            df = df.sort_values(by=["中心ID"]).reset_index(drop=True)
            if "中心ID" in df.columns:
                df = df.drop(columns=["中心ID"])

            if not df.empty:
                total_row = {"区县": "", "支撑中心": "成都总计"}
                best_row = {"区县": "", "支撑中心": "全市最优值"}
                for iid in ordered_ind_ids:
                    col_v = name_map.get(iid, f"指标{iid}")
                    col_s = f"{col_v}-得分"
                    series_v = pd.to_numeric(df[col_v], errors="coerce")
                    series_s = pd.to_numeric(df[col_s], errors="coerce")
                    total_row[col_v] = float(series_v.mean(skipna=True)) if series_v.size else None
                    total_row[col_s] = float(series_s.mean(skipna=True)) if series_s.size else None
                    if pos_map.get(iid, 1) == 1:
                        best_row[col_v] = float(series_v.max(skipna=True)) if series_v.size else None
                    else:
                        best_row[col_v] = float(series_v.min(skipna=True)) if series_v.size else None
                    best_row[col_s] = float(series_s.max(skipna=True)) if series_s.size else None
                df = pd.concat([df, pd.DataFrame([total_row, best_row])], ignore_index=True)

            df.to_excel(writer, index=False, sheet_name=str(stat_date))
            ws = writer.sheets[str(stat_date)]
            from openpyxl.styles import Font
            bold = Font(bold=True)
            for cell in ws[1]:
                cell.font = bold

    return buf.getvalue()


def build_district_pivot_xlsx(rows: list[dict]) -> bytes:
    if not rows:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame({"提示": ["无数据"]}).to_excel(writer, index=False, sheet_name="空")
        return buf.getvalue()

    ordered_ind_ids: list[int] = []
    name_map: dict[int, str] = {}
    pos_map: dict[int, int] = {}
    seen = set()
    for r in rows:
        iid = int(r.get("indicator_id"))
        if iid not in seen:
            ordered_ind_ids.append(iid)
            seen.add(iid)
        name_map[iid] = str(r.get("indicator_name") or f"指标{iid}")
        pos_map[iid] = int(r.get("is_positive") if r.get("is_positive") is not None else 1)

    group_by_date: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        group_by_date[str(r.get("stat_date"))].append(r)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for stat_date, date_rows in sorted(group_by_date.items()):
            agg: dict[int, dict[int, dict[str, float | None]]] = defaultdict(dict)
            extra_cols: dict[int, tuple[int, str]] = {}
            for r in date_rows:
                did = int(r.get("district_id"))
                iid = int(r.get("indicator_id"))
                val = r.get("value")
                sc = r.get("score")
                agg[did][iid] = {
                    "value": float(val) if val is not None else None,
                    "score": float(sc) if sc is not None else None,
                }
                extra_cols[did] = (int(r.get("circle_id") or 0), str(r.get("district_name") or ""))

            data = []
            for did, vals in agg.items():
                circle_id, dname = extra_cols.get(did, (0, ""))
                row = {"区县ID": did, "圈层": circle_id, "区县": dname}
                for iid in ordered_ind_ids:
                    col_name = name_map.get(iid, f"指标{iid}")
                    v = vals.get(iid) or {}
                    row[col_name] = v.get("value")
                    row[f"{col_name}-得分"] = v.get("score")
                data.append(row)

            df = pd.DataFrame(data)
            df = df.sort_values(by=["区县ID"]).reset_index(drop=True)
            if "区县ID" in df.columns:
                df = df.drop(columns=["区县ID"])

            if not df.empty:
                total_row = {"圈层": "", "区县": "成都总计"}
                best_row = {"圈层": "", "区县": "全市最优值"}
                for iid in ordered_ind_ids:
                    col_v = name_map.get(iid, f"指标{iid}")
                    col_s = f"{col_v}-得分"
                    series_v = pd.to_numeric(df[col_v], errors="coerce")
                    series_s = pd.to_numeric(df[col_s], errors="coerce")
                    total_row[col_v] = float(series_v.mean(skipna=True)) if series_v.size else None
                    total_row[col_s] = float(series_s.mean(skipna=True)) if series_s.size else None
                    if pos_map.get(iid, 1) == 1:
                        best_row[col_v] = float(series_v.max(skipna=True)) if series_v.size else None
                    else:
                        best_row[col_v] = float(series_v.min(skipna=True)) if series_v.size else None
                    best_row[col_s] = float(series_s.max(skipna=True)) if series_s.size else None
                df = pd.concat([df, pd.DataFrame([total_row, best_row])], ignore_index=True)

            df.to_excel(writer, index=False, sheet_name=str(stat_date))
            ws = writer.sheets[str(stat_date)]
            from openpyxl.styles import Font
            bold = Font(bold=True)
            for cell in ws[1]:
                cell.font = bold

    return buf.getvalue()
