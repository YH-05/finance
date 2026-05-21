"""notebook/FILING_NLP/*.ipynb を nbformat で生成するスクリプト.

実行方法::

    uv run python scripts/build_filing_nlp_notebooks.py

各 notebook のセル定義はこのファイル内で管理する。
セル内容を変更したい場合はここを編集して再実行すること。
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

OUT_DIR = Path(__file__).resolve().parent.parent / "notebook" / "FILING_NLP"


def _md(src: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(src)


def _code(src: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(src)


def _save(nb: nbf.NotebookNode, name: str) -> None:
    path = OUT_DIR / name
    nbf.write(nb, path)
    print(f"wrote: {path}")


# ---------------------------------------------------------------------------
# 01_fetch_and_chunk.ipynb
# ---------------------------------------------------------------------------


def build_01_fetch_and_chunk() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    }
    nb.cells = [
        _md(
            "# 01 Fetch & Chunk\n\n"
            "AAPL/MSFT/GOOGL の 10-K × 5年 + 10-Q × 15四半期 = 60 件を取得し、\n"
            "Item 1A (Risk Factors) と Item 7/Item 2 (MD&A) を抽出、\n"
            "FinBERT トークナイザで 510 トークンチャンクに分割する。"
        ),
        _code(
            "# Cell 1: imports + setup (必ず最初に _helpers を import)\n"
            "# Jupyter のモジュールキャッシュ対策: 古い _helpers / edgar を退避してから再 import\n"
            "import sys\n"
            "from pathlib import Path\n"
            "for _m in [m for m in list(sys.modules) if m == '_helpers' or m == 'edgar' or m.startswith('edgar.')]:\n"
            "    del sys.modules[_m]\n"
            "sys.path.insert(0, str(Path.cwd()))\n"
            "import _helpers\n"
            "_ = _helpers.setup_edgar()\n"
            "device = _helpers.get_device()\n"
            "print('device:', device)\n"
            "print('DATA_DIR:', _helpers.DATA_DIR)\n"
        ),
        _code(
            "# Cell 2: 10-K を 3 銘柄 × 5 年取得 (edgartools 直接利用)\n"
            "import edgar\n"
            "from concurrent.futures import ThreadPoolExecutor\n"
            "from tqdm.auto import tqdm\n"
            "\n"
            "TICKERS = ['AAPL', 'MSFT', 'GOOGL']\n"
            "\n"
            "def _fetch(ticker, form, limit):\n"
            "    try:\n"
            "        return ticker, list(edgar.Company(ticker).get_filings(form=form).head(limit))\n"
            "    except Exception as e:  # noqa: BLE001\n"
            "        return ticker, e\n"
            "\n"
            "with ThreadPoolExecutor(max_workers=3) as ex:\n"
            "    filings_10k = dict(ex.map(lambda t: _fetch(t, '10-K', 5), TICKERS))\n"
            "for t, r in filings_10k.items():\n"
            "    print(t, len(r) if not isinstance(r, Exception) else f'ERR: {r}')\n"
        ),
        _code(
            "# Cell 3: 10-Q を 3 銘柄 × 15 四半期取得\n"
            "with ThreadPoolExecutor(max_workers=3) as ex:\n"
            "    filings_10q = dict(ex.map(lambda t: _fetch(t, '10-Q', 15), TICKERS))\n"
            "for t, r in filings_10q.items():\n"
            "    print(t, len(r) if not isinstance(r, Exception) else f'ERR: {r}')\n"
        ),
        _code(
            "# Cell 4: filings メタを 1 つの DataFrame に統合し filings.parquet 保存\n"
            "import pandas as pd\n"
            "\n"
            "all_filing_objs = []\n"
            "for d, label in [(filings_10k, '10-K'), (filings_10q, '10-Q')]:\n"
            "    for ticker, result in d.items():\n"
            "        if isinstance(result, Exception):\n"
            "            continue\n"
            "        for f in result:\n"
            "            all_filing_objs.append((ticker, label, f))\n"
            "\n"
            "df_filings = pd.DataFrame([\n"
            "    {\n"
            "        'filing_id': str(f.accession_number),\n"
            "        'ticker': ticker,\n"
            "        'form': form,\n"
            "        'filing_date': pd.Timestamp(str(f.filing_date)),\n"
            "        'accession_number': str(f.accession_number),\n"
            "    }\n"
            "    for ticker, form, f in all_filing_objs\n"
            "])\n"
            "df_filings = df_filings.sort_values(['ticker', 'form', 'filing_date']).reset_index(drop=True)\n"
            "df_filings.to_parquet(_helpers.FILINGS_PARQUET)\n"
            "print('saved:', _helpers.FILINGS_PARQUET, 'rows:', len(df_filings))\n"
            "df_filings.head()\n"
        ),
        _code(
            "# Cell 5: 10-K のセクション抽出 (edgartools TenK ネイティブ accessor)\n"
            "# TenK.risk_factors -> Item 1A、 TenK.management_discussion -> Item 7\n"
            "section_rows = []\n"
            "miss = []\n"
            "for ticker, form, f in tqdm([x for x in all_filing_objs if x[1] == '10-K'], desc='10-K sections'):\n"
            "    try:\n"
            "        obj = f.obj()  # TenK インスタンス\n"
            "    except Exception as e:  # noqa: BLE001\n"
            "        print(f'10-K obj fail: {ticker} {f.accession_number} {e}')\n"
            "        continue\n"
            "    fid = str(f.accession_number)\n"
            "    for key, attr in [('item_1a', 'risk_factors'), ('item_7', 'management_discussion')]:\n"
            "        text = getattr(obj, attr, None)\n"
            "        if isinstance(text, str) and text:\n"
            "            section_rows.append({\n"
            "                'filing_id': fid, 'section_key': key,\n"
            "                'text': text, 'char_count': len(text),\n"
            "            })\n"
            "        else:\n"
            "            miss.append((ticker, fid, '10-K', key))\n"
            "print('10-K sections extracted:', len(section_rows), 'miss:', len(miss))\n"
        ),
        _code(
            "# Cell 6: 10-Q のセクション抽出 (edgartools TenQ ネイティブ subscript)\n"
            "# obj['Part II, Item 1A'] -> Risk Factors、 obj['Part I, Item 2'] -> MD&A\n"
            "for ticker, form, f in tqdm([x for x in all_filing_objs if x[1] == '10-Q'], desc='10-Q sections'):\n"
            "    try:\n"
            "        obj = f.obj()  # TenQ インスタンス\n"
            "    except Exception as e:  # noqa: BLE001\n"
            "        print(f'10-Q obj fail: {ticker} {f.accession_number} {e}')\n"
            "        continue\n"
            "    fid = str(f.accession_number)\n"
            "    for key, idx in [('item_1a', 'Part II, Item 1A'), ('item_7', 'Part I, Item 2')]:\n"
            "        try:\n"
            "            text = obj[idx]\n"
            "        except (KeyError, TypeError):\n"
            "            text = None\n"
            "        if isinstance(text, str) and text:\n"
            "            section_rows.append({\n"
            "                'filing_id': fid, 'section_key': key,\n"
            "                'text': text, 'char_count': len(text),\n"
            "            })\n"
            "        else:\n"
            "            miss.append((ticker, fid, '10-Q', key))\n"
            "print('total sections:', len(section_rows), 'total miss:', len(miss))\n"
        ),
        _code(
            "# Cell 7: sections.parquet 保存\n"
            "df_sections = pd.DataFrame(section_rows)\n"
            "df_sections.to_parquet(_helpers.SECTIONS_PARQUET)\n"
            "print('saved:', _helpers.SECTIONS_PARQUET, 'rows:', len(df_sections))\n"
            "df_sections.groupby('section_key').size()\n"
        ),
        _md(
            "## Cell 8: FinBERT トークナイザでチャンク化\n\n"
            "FinBERT (`yiyanghkust/finbert-tone`) は金融テキスト特化の BERT 派生モデル。\n"
            "**入力上限は 512 トークン**（CLS / SEP の特殊トークン込み）。\n"
            "この notebook ではセンチメント推論は行わず、tokenizer だけ使って\n"
            "section テキストを 510 トークンのスライディングウィンドウに分割する。\n"
            "推論は `02_finbert_sentiment.ipynb` で行う。"
        ),
        _code(
            "# Cell 8a: FinBERT トークナイザのロード\n"
            "# from_pretrained は HF_HOME (notebook/FILING_NLP/data/hf_cache) を見て\n"
            "# キャッシュがあればそれを、無ければ HuggingFace Hub から DL する。\n"
            "# tokenizer は数 KB のみ。重い model (~440MB) のロードはここでは不要。\n"
            "from transformers import AutoTokenizer\n"
            "\n"
            "FINBERT_MODEL_ID = 'yiyanghkust/finbert-tone'\n"
            "tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL_ID)\n"
            "print('tokenizer:', type(tokenizer).__name__)\n"
            "print('vocab_size:', tokenizer.vocab_size)\n"
            "print('model_max_length:', tokenizer.model_max_length)\n"
            "print('special tokens:', tokenizer.special_tokens_map)\n"
        ),
        _code(
            "# Cell 8b: スライディングウィンドウ・チャンク化関数\n"
            "# 設計:\n"
            "#   - max_tokens=510: 512 上限 - 2 (CLS + SEP) = 510 を 1 チャンクに収める\n"
            "#   - stride=128: 隣接チャンク間で 128 トークン重複させ、段落境界で文脈が\n"
            "#     途切れるのを緩和する (Risk Factors のような長文での hallucination を抑制)\n"
            "#\n"
            "# tokenizer の使い方:\n"
            "#   - tokenizer(text, add_special_tokens=False) で CLS/SEP 抜きの input_ids\n"
            "#   - tokenizer.decode(ids, skip_special_tokens=True) で再構築 (チャンク文字列を得る)\n"
            "#   - decode の境界はトークン単位なので、サブワードが切れることはない\n"
            "from tqdm.auto import tqdm\n"
            "\n"
            "MAX_TOKENS = 510\n"
            "STRIDE = 128\n"
            "\n"
            "def chunk_text(text: str, tokenizer, max_tokens: int = MAX_TOKENS, stride: int = STRIDE) -> list[str]:\n"
            "    if not text or not text.strip():\n"
            "        return []\n"
            "    token_ids = tokenizer(\n"
            "        text, add_special_tokens=False, truncation=False,\n"
            "        return_attention_mask=False,\n"
            "    )['input_ids']\n"
            "    if len(token_ids) <= max_tokens:\n"
            "        return [text]\n"
            "    step = max_tokens - stride  # 各チャンクで新規に進めるトークン数\n"
            "    if step <= 0:\n"
            "        raise ValueError(f'max_tokens ({max_tokens}) must exceed stride ({stride})')\n"
            "    chunks = []\n"
            "    start = 0\n"
            "    while start < len(token_ids):\n"
            "        window = token_ids[start : start + max_tokens]\n"
            "        chunks.append(tokenizer.decode(window, skip_special_tokens=True))\n"
            "        if start + max_tokens >= len(token_ids):\n"
            "            break\n"
            "        start += step\n"
            "    return chunks\n"
            "\n"
            "# 動作確認: df_sections の 1 件目で chunk 数と先頭の token 数を表示\n"
            "sample = df_sections.iloc[0]\n"
            "sample_chunks = chunk_text(sample['text'], tokenizer)\n"
            "print(f\"sample {sample['filing_id']} / {sample['section_key']} \"\n"
            "      f\"({sample['char_count']} chars) -> {len(sample_chunks)} chunks\")\n"
            "for i, c in enumerate(sample_chunks[:3]):\n"
            "    n_tok = len(tokenizer.encode(c, add_special_tokens=False))\n"
            "    print(f'  chunk[{i}] {n_tok} tokens | head: {c[:80]!r}')\n"
        ),
        _code(
            "# Cell 8c: 全 section に chunk_text を適用 → chunk_rows を構築\n"
            "chunk_rows = []\n"
            "for row in tqdm(df_sections.to_dict('records'), desc='chunking'):\n"
            "    chunks = chunk_text(row['text'], tokenizer)\n"
            "    for i, c in enumerate(chunks):\n"
            "        chunk_rows.append({\n"
            "            'filing_id': row['filing_id'],\n"
            "            'section_key': row['section_key'],\n"
            "            'chunk_idx': i,\n"
            "            'text': c,\n"
            "            'token_count': len(tokenizer.encode(c, add_special_tokens=False)),\n"
            "        })\n"
            "print('total chunks:', len(chunk_rows))\n"
        ),
        _code(
            "# Cell 9: chunks.parquet 保存 + ticker/form 結合\n"
            "df_chunks = pd.DataFrame(chunk_rows).merge(\n"
            "    df_filings[['filing_id', 'ticker', 'form', 'filing_date']],\n"
            "    on='filing_id', how='left',\n"
            ")\n"
            "df_chunks.to_parquet(_helpers.CHUNKS_PARQUET)\n"
            "print('saved:', _helpers.CHUNKS_PARQUET, 'rows:', len(df_chunks))\n"
            "df_chunks.groupby(['ticker', 'form', 'section_key']).size()\n"
        ),
        _md(
            "## Cell 10: 企業名エンティティ抽出 (NER)\n\n"
            "FinBERT (finbert-tone) は sequence classification のみで NER 非対応のため、\n"
            "ここでは **`dslim/bert-base-NER`** を使う。これは CoNLL-2003 で fine-tune\n"
            "された BERT で、4 ラベル (**ORG / PER / LOC / MISC**) の **token-level**\n"
            "分類モデル (`AutoModelForTokenClassification`)。サイズ ~110MB。\n\n"
            "10-K/10-Q から **ORG (企業名・組織名)** を抽出する。入力は `chunks.parquet`\n"
            "の chunk (510 トークン以下に分割済み) を使うことで BERT の 512 トークン\n"
            "上限に確実に収める。"
        ),
        _code(
            "# Cell 10a: NER モデルのロード (pipeline 経由)\n"
            "# transformers.pipeline は AutoTokenizer + AutoModelForTokenClassification を\n"
            "# 内部で組み立てる。aggregation_strategy='simple' でサブワード ('Goog' + '##le')\n"
            "# を 1 word ('Google') にまとめてくれる。\n"
            "#\n"
            "# device 指定: pipeline は torch device の番号 (int) または 'mps' 文字列を\n"
            "# 取る。get_device() の戻り値が torch.device('mps') の場合は str() で 'mps' に。\n"
            "import pandas as pd\n"
            "from transformers import pipeline\n"
            "\n"
            "# カーネル再起動後でも単独実行できるよう df_chunks を再ロード\n"
            "if 'df_chunks' not in globals():\n"
            "    df_chunks = pd.read_parquet(_helpers.CHUNKS_PARQUET)\n"
            "    print('df_chunks loaded from parquet:', len(df_chunks), 'rows')\n"
            "\n"
            "NER_MODEL_ID = 'dslim/bert-base-NER'\n"
            "ner = pipeline(\n"
            "    'ner', model=NER_MODEL_ID, tokenizer=NER_MODEL_ID,\n"
            "    aggregation_strategy='simple',\n"
            "    device=str(device) if str(device) == 'mps' else -1,\n"
            ")\n"
            "print('NER model:', NER_MODEL_ID)\n"
            "print('id2label:', ner.model.config.id2label)\n"
        ),
        _code(
            "# Cell 10b: サンプル 1 chunk で動作確認 (ORG エンティティを表示)\n"
            "# pipeline 出力: list[dict] で、各 dict は\n"
            "#   {'entity_group': 'ORG', 'score': 0.99, 'word': 'Apple Inc.',\n"
            "#    'start': 12, 'end': 22}\n"
            "# のような形式。start/end は元テキストの文字オフセット。\n"
            "sample_chunk = df_chunks.iloc[0]\n"
            "sample_ents = ner(sample_chunk['text'])\n"
            "orgs = [e for e in sample_ents if e['entity_group'] == 'ORG']\n"
            "print(f\"sample {sample_chunk['filing_id']} / {sample_chunk['section_key']} \"\n"
            "      f\"chunk[{sample_chunk['chunk_idx']}] → {len(orgs)} ORG entities\")\n"
            "for e in orgs[:10]:\n"
            "    print(f\"  {e['word']!r} score={e['score']:.3f} pos=[{e['start']}:{e['end']}]\")\n"
        ),
        _code(
            "# Cell 10c: 全 chunks に NER を適用 → ORG だけ entities.parquet に保存\n"
            "# pipeline はリスト入力でバッチ推論できる。batch_size で内部マイクロバッチを制御。\n"
            "# tqdm で進捗を見せるため chunk 単位ループにする (バッチ間で進捗 update)。\n"
            "BATCH_SIZE = 16\n"
            "entity_rows = []\n"
            "texts = df_chunks['text'].tolist()\n"
            "meta = df_chunks[['filing_id','ticker','form','section_key','chunk_idx']].to_dict('records')\n"
            "\n"
            "for start in tqdm(range(0, len(texts), BATCH_SIZE), desc='ner'):\n"
            "    batch_texts = texts[start:start+BATCH_SIZE]\n"
            "    # pipeline はリストを受けると list[list[dict]] を返す\n"
            "    batch_results = ner(batch_texts)\n"
            "    for i, ents in enumerate(batch_results):\n"
            "        m = meta[start + i]\n"
            "        for e in ents:\n"
            "            if e['entity_group'] != 'ORG':\n"
            "                continue\n"
            "            entity_rows.append({\n"
            "                'filing_id': m['filing_id'],\n"
            "                'ticker': m['ticker'],\n"
            "                'form': m['form'],\n"
            "                'section_key': m['section_key'],\n"
            "                'chunk_idx': m['chunk_idx'],\n"
            "                'org': e['word'].strip(),\n"
            "                'score': float(e['score']),\n"
            "                'start': int(e['start']),\n"
            "                'end': int(e['end']),\n"
            "            })\n"
            "\n"
            "df_entities = pd.DataFrame(entity_rows)\n"
            "df_entities.to_parquet(_helpers.ENTITIES_PARQUET)\n"
            "print('saved:', _helpers.ENTITIES_PARQUET, 'rows:', len(df_entities))\n"
            "# 出現頻度 top 20\n"
            "df_entities['org'].str.lower().value_counts().head(20)\n"
        ),
        _md(
            "## Cell 11: GLiNER による Zero-shot NER (より高精度)\n\n"
            "`urchade/gliner_large-v2.1` は **任意のラベル名を文字列で指定できる**\n"
            "zero-shot NER モデル (DeBERTa-v3-large ベース、~1.7GB)。\n"
            "10-K 特有の `'the Company'` ノイズを避けるために、\n"
            "**'public company name' / 'subsidiary' / 'auditor' / 'regulator'**\n"
            "といった意味的に区別したラベルを指定する。dslim/bert-base-NER の\n"
            "結果 (`entities.parquet`) と比較できるよう、出力は別ファイル\n"
            "`entities_gliner.parquet` に保存する。\n\n"
            "**事前準備**: `uv sync` で `gliner` パッケージをインストールしておく。"
        ),
        _code(
            "# Cell 11a: GLiNER モデルのロード + サンプル動作確認\n"
            "# from_pretrained は HuggingFace Hub から ~1.7GB DL する (HF_HOME に保存)。\n"
            "# 初回ロードは数分かかる。to(device) で MPS / CPU に移動。\n"
            "import pandas as pd\n"
            "from gliner import GLiNER\n"
            "\n"
            "# カーネル再起動後でも単独実行できるよう df_chunks / chunk_text を保証\n"
            "if 'df_chunks' not in globals():\n"
            "    df_chunks = pd.read_parquet(_helpers.CHUNKS_PARQUET)\n"
            "    print('df_chunks loaded from parquet:', len(df_chunks), 'rows')\n"
            "if 'chunk_text' not in globals():\n"
            "    # Cell 8b を skip した場合のフォールバック: _helpers の同等関数を使う\n"
            "    from _helpers import chunk_text\n"
            "    print('chunk_text imported from _helpers')\n"
            "\n"
            "GLINER_MODEL_ID = 'urchade/gliner_large-v2.1'\n"
            "gliner_model = GLiNER.from_pretrained(GLINER_MODEL_ID)\n"
            "gliner_model = gliner_model.to(device)\n"
            "\n"
            "# ラベル設計の意図:\n"
            "#   - public company name: 上場企業 (Apple Inc., Microsoft 等) ← 主要ターゲット\n"
            "#   - subsidiary: 子会社・関連会社\n"
            "#   - auditor: 監査法人 (PricewaterhouseCoopers 等)\n"
            "#   - regulator: 規制機関 (SEC, FED, EU Commission)\n"
            "# 'the Company' のような代名詞は意味的にどのラベルにも合わないため除外されやすい。\n"
            "GLINER_LABELS = ['public company name', 'subsidiary', 'auditor', 'regulator']\n"
            "# threshold: 0.5 だと 'Company' (代名詞用法) が大量にヒットする。0.7 以上に\n"
            "# 上げると noise が大幅減。さらに上げると recall が落ちる。試行錯誤推奨。\n"
            "GLINER_THRESHOLD = 0.7\n"
            "\n"
            "# サンプル動作確認\n"
            "sample_chunk = df_chunks.iloc[0]\n"
            "sample_ents = gliner_model.predict_entities(\n"
            "    sample_chunk['text'], GLINER_LABELS, threshold=GLINER_THRESHOLD,\n"
            ")\n"
            "print(f\"sample {sample_chunk['filing_id']} / {sample_chunk['section_key']} \"\n"
            "      f\"chunk[{sample_chunk['chunk_idx']}] → {len(sample_ents)} entities\")\n"
            "for e in sample_ents[:10]:\n"
            "    print(f\"  [{e['label']}] {e['text']!r} score={e['score']:.3f} \"\n"
            "          f\"pos=[{e['start']}:{e['end']}]\")\n"
        ),
        _code(
            "# Cell 11b: 全 chunks に GLiNER 適用 → entities_gliner.parquet 保存\n"
            "#\n"
            "# 注意点 1: GLiNER は内部 max_len=384 で train されているため、\n"
            "#   chunks.parquet の 510 トークン chunk を直接渡すと truncation 警告が出る。\n"
            "#   ここでは GLiNER 内部 tokenizer + chunk_text() (Cell 8b 定義) で\n"
            "#   各 chunk を 350 トークン以下に再分割してから推論する。\n"
            "# 注意点 2: GLiNER 新 API は inference(...) (batch_predict_entities は\n"
            "#   FutureWarning で deprecated)。inference は list[str] を受け取る。\n"
            "\n"
            "# GLiNER 内部 tokenizer (DeBERTa-v3-large) を取り出す\n"
            "gliner_tok = gliner_model.data_processor.transformer_tokenizer\n"
            "GLINER_MAX_TOKENS = 350  # 384 上限に safety margin\n"
            "GLINER_STRIDE = 64\n"
            "\n"
            "# 各 chunk を GLiNER 用にさらに再分割\n"
            "expanded_meta = []\n"
            "expanded_texts = []\n"
            "for row in df_chunks.itertuples():\n"
            "    sub_chunks = chunk_text(row.text, gliner_tok,\n"
            "                            max_tokens=GLINER_MAX_TOKENS, stride=GLINER_STRIDE)\n"
            "    for sub_idx, sc in enumerate(sub_chunks):\n"
            "        expanded_meta.append({\n"
            "            'filing_id': row.filing_id, 'ticker': row.ticker, 'form': row.form,\n"
            "            'section_key': row.section_key, 'chunk_idx': row.chunk_idx,\n"
            "            'sub_idx': sub_idx,\n"
            "        })\n"
            "        expanded_texts.append(sc)\n"
            "print(f'expanded {len(df_chunks)} chunks -> {len(expanded_texts)} sub-chunks for GLiNER')\n"
            "\n"
            "# バッチ推論 (inference は 1 度に list[str] を受ける。tqdm 進捗のため\n"
            "# 外側で BATCH_SIZE 件ずつスライス呼び出し)\n"
            "BATCH_SIZE = 8  # GLiNER large は重いので小さめ\n"
            "entity_rows = []\n"
            "for start in tqdm(range(0, len(expanded_texts), BATCH_SIZE), desc='gliner'):\n"
            "    batch_texts = expanded_texts[start:start+BATCH_SIZE]\n"
            "    batch_results = gliner_model.inference(\n"
            "        batch_texts, GLINER_LABELS,\n"
            "        threshold=GLINER_THRESHOLD, batch_size=BATCH_SIZE,\n"
            "    )\n"
            "    for i, ents in enumerate(batch_results):\n"
            "        m = expanded_meta[start + i]\n"
            "        for e in ents:\n"
            "            entity_rows.append({\n"
            "                'filing_id': m['filing_id'],\n"
            "                'ticker': m['ticker'],\n"
            "                'form': m['form'],\n"
            "                'section_key': m['section_key'],\n"
            "                'chunk_idx': m['chunk_idx'],\n"
            "                'sub_idx': m['sub_idx'],\n"
            "                'label': e['label'],\n"
            "                'org': e['text'].strip(),\n"
            "                'score': float(e['score']),\n"
            "                'start': int(e['start']),  # sub-chunk 内オフセット\n"
            "                'end': int(e['end']),\n"
            "            })\n"
            "\n"
            "df_gliner = pd.DataFrame(entity_rows)\n"
            "df_gliner.to_parquet(_helpers.ENTITIES_GLINER_PARQUET)\n"
            "print('saved:', _helpers.ENTITIES_GLINER_PARQUET, 'rows:', len(df_gliner))\n"
            "# ラベル別件数\n"
            "print('label dist:'); print(df_gliner['label'].value_counts())\n"
            "# public company name の頻度 top 20\n"
            "print('top public companies:')\n"
            "df_gliner[df_gliner['label']=='public company name']['org'].str.lower().value_counts().head(20)\n"
        ),
    ]
    return nb


# ---------------------------------------------------------------------------
# 02_finbert_sentiment.ipynb
# ---------------------------------------------------------------------------


def build_02_finbert_sentiment() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    }
    nb.cells = [
        _md(
            "# 02 FinBERT Sentiment\n\n"
            "`chunks.parquet` を読み込み、FinBERT (`yiyanghkust/finbert-tone`) で\n"
            "各チャンクの positive / negative / neutral 確率を推論する。\n"
            "filing × section 単位で集約して可視化。\n\n"
            "FinBERT は **金融テキスト特化の BERT-base** を `Sequence Classification`\n"
            "(3 ラベル) で fine-tune したモデル。入力上限は **512 トークン**、出力は\n"
            "`{Neutral, Positive, Negative}` の確率分布 (softmax)。"
        ),
        _code(
            "# Cell 1: imports + setup\n"
            "import sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path.cwd()))\n"
            "import _helpers\n"
            "import torch\n"
            "import pandas as pd\n"
            "from tqdm.auto import tqdm\n"
            "\n"
            "device = _helpers.get_device()\n"
            "print('device:', device)\n"
        ),
        _md(
            "## Cell 2: FinBERT モデルとトークナイザを直接ロード\n\n"
            "`AutoTokenizer.from_pretrained` で tokenizer、\n"
            "`AutoModelForSequenceClassification.from_pretrained` で分類モデル本体を\n"
            "ロードする (Hugging Face Hub から、HF_HOME に既にキャッシュされていれば\n"
            "そこから読む)。\n\n"
            "**`AutoModelForSequenceClassification`** は文・段落単位を 1 ベクトル化\n"
            "([CLS] トークンの埋め込み) して N クラス分類するためのヘッド付きモデル\n"
            "クラス。NER (token-level) や embedding 専用とは別物。\n\n"
            "ロード後は:\n"
            "- `.to(device)` で GPU/MPS に移動\n"
            "- `.eval()` で **学習用 dropout を無効化** (推論時は必須)\n"
            "- `model.config.id2label` で出力ラベル名を確認"
        ),
        _code(
            "# Cell 2: FinBERT (yiyanghkust/finbert-tone) を直接ロード\n"
            "from transformers import AutoModelForSequenceClassification, AutoTokenizer\n"
            "\n"
            "FINBERT_MODEL_ID = 'yiyanghkust/finbert-tone'\n"
            "\n"
            "tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL_ID)\n"
            "model = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL_ID)\n"
            "model.to(device)\n"
            "model.eval()  # 推論モード (dropout を無効化)\n"
            "\n"
            "print('model:', type(model).__name__)\n"
            "print('num_labels:', model.config.num_labels)\n"
            "print('id2label:', model.config.id2label)\n"
            "print('hidden_size:', model.config.hidden_size)\n"
            "print('max position embeddings:', model.config.max_position_embeddings)\n"
        ),
        _code(
            "# Cell 3: chunks 読み込み (01 で保存した chunks.parquet を入力に使う)\n"
            "df_chunks = pd.read_parquet(_helpers.CHUNKS_PARQUET)\n"
            "print('chunks:', len(df_chunks))\n"
            "df_chunks.head(3)\n"
        ),
        _md(
            "## Cell 4: FinBERT 推論ループ (バッチ処理)\n\n"
            "全 chunk テキストを `BATCH_SIZE=32` 件ずつまとめて推論する。\n\n"
            "**ステップ**:\n"
            "1. `tokenizer(batch, padding=True, truncation=True, max_length=512,\n"
            "   return_tensors='pt')` でテキスト → tensor。`padding=True` でバッチ内\n"
            "   最長に合わせ、`truncation=True` で 512 を超える分を切る。\n"
            "2. `.to(device)` で MPS / CPU に転送。\n"
            "3. `torch.no_grad()` で **勾配計算を無効** にして高速化 + メモリ節約。\n"
            "4. `model(**enc)` で `logits` (生スコア、形状 [B, 3]) を得る。\n"
            "5. `.softmax(dim=-1)` で確率分布 (合計 1.0) に変換。\n"
            "6. `.cpu().numpy()` で NumPy 配列に持ってくる。\n\n"
            "**id2label の順序** (Neutral=0 / Positive=1 / Negative=2) はモデルに依存\n"
            "するため、固定 index で扱わず Cell 5 で `id2label` を介して pos/neg/neu に\n"
            "再マッピングする。"
        ),
        _code(
            "# Cell 4: バッチ推論 (pos/neg/neu の確率を all_probs に蓄積)\n"
            "BATCH_SIZE = 32\n"
            "id2label = model.config.id2label  # {0: 'Neutral', 1: 'Positive', 2: 'Negative'}\n"
            "label_names = [id2label[i] for i in range(len(id2label))]\n"
            "\n"
            "all_probs = []\n"
            "texts = df_chunks['text'].tolist()\n"
            "for start in tqdm(range(0, len(texts), BATCH_SIZE), desc='finbert'):\n"
            "    batch = texts[start:start+BATCH_SIZE]\n"
            "    enc = tokenizer(\n"
            "        batch,\n"
            "        padding=True, truncation=True, max_length=512,\n"
            "        return_tensors='pt',\n"
            "    ).to(device)\n"
            "    with torch.no_grad():\n"
            "        out = model(**enc)\n"
            "    probs = out.logits.softmax(dim=-1).cpu().numpy()\n"
            "    all_probs.extend(probs.tolist())\n"
            "print('done. samples:', len(all_probs), 'label_names:', label_names)\n"
        ),
        _code(
            "# Cell 5: sentiments.parquet 保存 (id2label の順序に依らず pos/neg/neu 列で揃える)\n"
            "import numpy as np\n"
            "probs_arr = np.array(all_probs)\n"
            "# ラベル名 → 列 index の写像を作り、明示的に pos/neg/neu の 3 列に再配置\n"
            "name2idx = {n.lower(): i for i, n in enumerate(label_names)}\n"
            "df_sent = df_chunks[['filing_id','ticker','form','section_key','chunk_idx','filing_date']].copy()\n"
            "df_sent['pos'] = probs_arr[:, name2idx['positive']]\n"
            "df_sent['neg'] = probs_arr[:, name2idx['negative']]\n"
            "df_sent['neu'] = probs_arr[:, name2idx['neutral']]\n"
            "df_sent['label'] = [label_names[i] for i in probs_arr.argmax(axis=1)]\n"
            "df_sent.to_parquet(_helpers.SENTIMENTS_PARQUET)\n"
            "print('saved:', _helpers.SENTIMENTS_PARQUET, 'rows:', len(df_sent))\n"
            "df_sent.head()\n"
        ),
        _code(
            "# Cell 6: filing × section 単位で平均センチメント集約\n"
            "agg = df_sent.groupby(['ticker','form','section_key','filing_id','filing_date'])[['pos','neg','neu']].mean().reset_index()\n"
            "agg = agg.sort_values(['ticker','section_key','filing_date'])\n"
            "agg.head(10)\n"
        ),
        _code(
            "# Cell 7: AAPL の Risk Factors (Item 1A) の neg スコア推移\n"
            "import plotly.express as px\n"
            "aapl_risk = agg[(agg['ticker']=='AAPL') & (agg['section_key']=='item_1a')].copy()\n"
            "fig = px.line(\n"
            "    aapl_risk, x='filing_date', y='neg', color='form', markers=True,\n"
            "    title='AAPL Risk Factors (Item 1A) - FinBERT negative score over time',\n"
            ")\n"
            "fig.show()\n"
        ),
        _code(
            "# Cell 8: 3 銘柄 × MD&A センチメント比較 (pos - neg)\n"
            "mda = agg[agg['section_key']=='item_7'].copy()\n"
            "mda['net_sentiment'] = mda['pos'] - mda['neg']\n"
            "fig = px.line(\n"
            "    mda, x='filing_date', y='net_sentiment', color='ticker', markers=True, line_dash='form',\n"
            "    title='MD&A net sentiment (pos - neg) by ticker/form',\n"
            ")\n"
            "fig.show()\n"
        ),
    ]
    return nb


# ---------------------------------------------------------------------------
# 03_embedding_analysis.ipynb
# ---------------------------------------------------------------------------


def build_03_embedding_analysis() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    }
    nb.cells = [
        _md(
            "# 03 Embedding Analysis\n\n"
            "`chunks.parquet` を BAAI/bge-large-en-v1.5 で 1024 次元 embedding 化し、\n"
            "1) 同一銘柄・同一セクションの年次変化検知\n"
            "2) UMAP による 2D 投影クラスタリング\n"
            "3) 銘柄間類似度比較\n"
            "を行う。"
        ),
        _code(
            "# Cell 1: imports + embedder ロード\n"
            "import sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path.cwd()))\n"
            "import _helpers\n"
            "import numpy as np\n"
            "import pandas as pd\n"
            "from tqdm.auto import tqdm\n"
            "\n"
            "device = _helpers.get_device()\n"
            "model = _helpers.load_embedder(device)\n"
            "print('device:', device, 'dim:', model.get_sentence_embedding_dimension())\n"
        ),
        _code(
            "# Cell 2: chunks 読み込み\n"
            "df_chunks = pd.read_parquet(_helpers.CHUNKS_PARQUET)\n"
            "print('chunks:', len(df_chunks))\n"
        ),
        _code(
            "# Cell 3: バッチ encode (normalize_embeddings=True で cos sim = dot product)\n"
            "vectors = model.encode(\n"
            "    df_chunks['text'].tolist(),\n"
            "    batch_size=16, show_progress_bar=True,\n"
            "    normalize_embeddings=True,\n"
            ")\n"
            "print('vectors shape:', vectors.shape)\n"
        ),
        _code(
            "# Cell 4: embeddings.parquet 保存 (vector 列は list[float])\n"
            "df_emb = df_chunks[['filing_id','ticker','form','section_key','chunk_idx','filing_date']].copy()\n"
            "df_emb['vector'] = list(vectors)\n"
            "df_emb.to_parquet(_helpers.EMBEDDINGS_PARQUET)\n"
            "print('saved:', _helpers.EMBEDDINGS_PARQUET, 'rows:', len(df_emb))\n"
        ),
        _code(
            "# Cell 5: filing × section 単位で平均プーリング → コサイン類似度 (前期比)\n"
            "def _avg_pool(group):\n"
            "    return np.mean(np.vstack(group['vector'].values), axis=0)\n"
            "\n"
            "pooled = (\n"
            "    df_emb.groupby(['ticker','form','section_key','filing_id','filing_date'])\n"
            "    .apply(lambda g: pd.Series({'mean_vec': _avg_pool(g)}))\n"
            "    .reset_index()\n"
            ")\n"
            "pooled = pooled.sort_values(['ticker','form','section_key','filing_date']).reset_index(drop=True)\n"
            "\n"
            "rows = []\n"
            "for (ticker, form, section), g in pooled.groupby(['ticker','form','section_key']):\n"
            "    g = g.sort_values('filing_date').reset_index(drop=True)\n"
            "    for i in range(1, len(g)):\n"
            "        v_prev = g.loc[i-1, 'mean_vec']\n"
            "        v_now = g.loc[i, 'mean_vec']\n"
            "        cos = float(np.dot(v_prev, v_now) / (np.linalg.norm(v_prev)*np.linalg.norm(v_now)))\n"
            "        rows.append({\n"
            "            'ticker': ticker, 'form': form, 'section_key': section,\n"
            "            'filing_date': g.loc[i, 'filing_date'],\n"
            "            'cos_sim_prev': cos,\n"
            "            'diff_score': 1.0 - cos,\n"
            "        })\n"
            "df_change = pd.DataFrame(rows)\n"
            "df_change.head()\n"
        ),
        _code(
            "# Cell 6: 変化検知の可視化 (Item 1A の前期比 diff 推移)\n"
            "import plotly.express as px\n"
            "risk_diff = df_change[df_change['section_key']=='item_1a']\n"
            "fig = px.line(\n"
            "    risk_diff, x='filing_date', y='diff_score', color='ticker', markers=True, line_dash='form',\n"
            "    title='Risk Factors (Item 1A) - cosine distance to previous filing',\n"
            ")\n"
            "fig.show()\n"
        ),
        _code(
            "# Cell 7: UMAP 2D 投影 (ticker で色分け)\n"
            "import umap\n"
            "X = np.vstack(pooled['mean_vec'].values)\n"
            "reducer = umap.UMAP(n_components=2, metric='cosine', random_state=42)\n"
            "X2 = reducer.fit_transform(X)\n"
            "pooled_plot = pooled.copy()\n"
            "pooled_plot['x'] = X2[:,0]\n"
            "pooled_plot['y'] = X2[:,1]\n"
            "fig = px.scatter(\n"
            "    pooled_plot, x='x', y='y', color='ticker', symbol='section_key',\n"
            "    hover_data=['form','filing_date'],\n"
            "    title='UMAP projection of filing×section embeddings',\n"
            ")\n"
            "fig.show()\n"
        ),
        _code(
            "# Cell 8: 類似銘柄 - AAPL 最新 10-K Item 1A vs MSFT/GOOGL 最新 Item 1A\n"
            "latest_risk = (\n"
            "    pooled[(pooled['form']=='10-K') & (pooled['section_key']=='item_1a')]\n"
            "    .sort_values('filing_date').groupby('ticker').tail(1).reset_index(drop=True)\n"
            ")\n"
            "vecs = {row['ticker']: row['mean_vec'] for _, row in latest_risk.iterrows()}\n"
            "import itertools\n"
            "sim_rows = []\n"
            "for a, b in itertools.combinations(vecs.keys(), 2):\n"
            "    cos = float(np.dot(vecs[a], vecs[b]) / (np.linalg.norm(vecs[a])*np.linalg.norm(vecs[b])))\n"
            "    sim_rows.append({'a': a, 'b': b, 'cosine': cos})\n"
            "pd.DataFrame(sim_rows).sort_values('cosine', ascending=False)\n"
        ),
    ]
    return nb


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    _save(build_01_fetch_and_chunk(), "01_fetch_and_chunk.ipynb")
    _save(build_02_finbert_sentiment(), "02_finbert_sentiment.ipynb")
    _save(build_03_embedding_analysis(), "03_embedding_analysis.ipynb")
    print("01, 02, 03 done.")
