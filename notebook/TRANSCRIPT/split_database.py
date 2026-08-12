"""split_db.py"""

import hashlib
import zipfile
from pathlib import Path


def split_db_to_zips(
    db_path: str,
    output_dir: str,
    n_parts: int,
) -> list[Path]:
    """
    DBファイルをn個に分割し、それぞれをZIP圧縮する

    Args:
        db_path: 分割対象のDBファイル
        output_dir: 出力先ディレクトリ
        n_parts: 分割数

    Returns:
        作成したZIPファイルパスのリスト
    """
    db_path = Path(db_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        raise FileNotFoundError(f"DBファイルが見つかりません: {db_path}")

    # 全体を読み込み
    data = db_path.read_bytes()
    total_size = len(data)
    chunk_size = (total_size + n_parts - 1) // n_parts  # 切り上げ

    # ハッシュ計算（復元時の検証用）
    original_hash = hashlib.sha256(data).hexdigest()

    print(f"📦 元ファイル: {db_path.name} ({total_size / 1024 / 1024:.2f} MB)")
    print(f"🔨 {n_parts}分割 (各 約 {chunk_size / 1024 / 1024:.2f} MB)")

    zip_paths = []
    for i in range(n_parts):
        start = i * chunk_size
        end = min(start + chunk_size, total_size)
        chunk = data[start:end]

        if not chunk:  # データが尽きた場合
            break

        # ZIP作成
        part_name = f"{db_path.stem}.part{i + 1:02d}"
        zip_path = output_dir / f"{part_name}.zip"

        with zipfile.ZipFile(
            zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9
        ) as zf:
            zf.writestr(part_name, chunk)

        zip_paths.append(zip_path)
        print(
            f"  ✅ {zip_path.name}: "
            f"{len(chunk) / 1024 / 1024:.2f} MB → "
            f"{zip_path.stat().st_size / 1024 / 1024:.2f} MB (圧縮後)"
        )

    # メタデータ保存（復元時に必要）
    manifest_path = output_dir / f"{db_path.stem}.manifest.txt"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(f"original_file={db_path.name}\n")
        f.write(f"total_size={total_size}\n")
        f.write(f"n_parts={len(zip_paths)}\n")
        f.write(f"sha256={original_hash}\n")
        for i, zp in enumerate(zip_paths):
            f.write(f"part{i + 1:02d}={zp.name}\n")

    print(f"📄 マニフェスト: {manifest_path}")
    print(
        f"🎉 完了: 合計 {sum(p.stat().st_size for p in zip_paths) / 1024 / 1024:.2f} MB"
    )

    return zip_paths


def restore_db_from_zips(
    manifest_path: str,
    output_path: str = "transcripts_restored.db",
) -> Path:
    """
    分割ZIPからDBファイルを復元する

    Args:
        manifest_path: マニフェストファイルのパス
        output_path: 復元先のDBファイルパス

    Returns:
        復元したDBファイルのパス
    """
    manifest_path = Path(manifest_path)
    output_path = Path(output_path)

    if not manifest_path.exists():
        raise FileNotFoundError(f"マニフェストが見つかりません: {manifest_path}")

    # マニフェスト読み込み
    meta = {}
    parts = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.startswith("part"):
                parts.append(value)
            else:
                meta[key] = value

    print(f"📖 マニフェスト読み込み: {len(parts)}パーツ")

    # 各ZIPを展開して結合
    base_dir = manifest_path.parent
    chunks = []
    for part_zip in parts:
        zip_path = base_dir / part_zip
        with zipfile.ZipFile(zip_path, "r") as zf:
            # ZIP内のファイル名を取得（1つだけ入っている想定）
            names = zf.namelist()
            if len(names) != 1:
                raise ValueError(f"予期しないZIP構造: {zip_path}")
            chunks.append(zf.read(names[0]))
        print(f"  📂 {zip_path.name} 展開完了")

    # 結合
    data = b"".join(chunks)

    # サイズ検証
    expected_size = int(meta.get("total_size", 0))
    if expected_size and len(data) != expected_size:
        raise ValueError(f"サイズ不一致: 期待 {expected_size} / 実際 {len(data)}")

    # ハッシュ検証
    expected_hash = meta.get("sha256")
    if expected_hash:
        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(
                f"ハッシュ不一致:\n  期待: {expected_hash}\n  実際: {actual_hash}"
            )
        print("  ✅ SHA256ハッシュ検証OK")

    # 書き出し
    output_path.write_bytes(data)
    print(f"🎉 復元完了: {output_path} ({len(data) / 1024 / 1024:.2f} MB)")

    return output_path
