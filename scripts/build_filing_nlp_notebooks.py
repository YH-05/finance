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
            "`chunks.parquet` を読み込み、FinBERT (yiyanghkust/finbert-tone) で\n"
            "各チャンクの positive / negative / neutral 確率を推論する。\n"
            "filing × section 単位で集約して可視化。"
        ),
        _code(
            "# Cell 1: imports + FinBERT ロード\n"
            "import sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path.cwd()))\n"
            "import _helpers\n"
            "import torch\n"
            "import pandas as pd\n"
            "from tqdm.auto import tqdm\n"
            "\n"
            "device = _helpers.get_device()\n"
            "tokenizer, model = _helpers.load_finbert(device)\n"
            "print('device:', device, 'labels:', model.config.id2label)\n"
        ),
        _code(
            "# Cell 2: chunks 読み込み\n"
            "df_chunks = pd.read_parquet(_helpers.CHUNKS_PARQUET)\n"
            "print('chunks:', len(df_chunks))\n"
            "df_chunks.head(3)\n"
        ),
        _code(
            "# Cell 3: バッチ推論 (pos/neg/neu)\n"
            "BATCH_SIZE = 32\n"
            "id2label = model.config.id2label\n"
            "label_names = [id2label[i] for i in range(len(id2label))]\n"
            "\n"
            "all_probs = []\n"
            "texts = df_chunks['text'].tolist()\n"
            "for start in tqdm(range(0, len(texts), BATCH_SIZE), desc='finbert'):\n"
            "    batch = texts[start:start+BATCH_SIZE]\n"
            "    enc = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors='pt').to(device)\n"
            "    with torch.no_grad():\n"
            "        out = model(**enc)\n"
            "    probs = out.logits.softmax(dim=-1).cpu().numpy()\n"
            "    all_probs.extend(probs.tolist())\n"
            "print('done. samples:', len(all_probs))\n"
        ),
        _code(
            "# Cell 4: sentiments.parquet 保存\n"
            "import numpy as np\n"
            "probs_arr = np.array(all_probs)\n"
            "# 列名を明示的に pos/neg/neu に統一\n"
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
            "# Cell 5: filing × section 単位で平均センチメント集約\n"
            "agg = df_sent.groupby(['ticker','form','section_key','filing_id','filing_date'])[['pos','neg','neu']].mean().reset_index()\n"
            "agg = agg.sort_values(['ticker','section_key','filing_date'])\n"
            "agg.head(10)\n"
        ),
        _code(
            "# Cell 6: AAPL の Risk Factors (Item 1A) の neg スコア推移\n"
            "import plotly.express as px\n"
            "aapl_risk = agg[(agg['ticker']=='AAPL') & (agg['section_key']=='item_1a')].copy()\n"
            "fig = px.line(\n"
            "    aapl_risk, x='filing_date', y='neg', color='form', markers=True,\n"
            "    title='AAPL Risk Factors (Item 1A) - FinBERT negative score over time',\n"
            ")\n"
            "fig.show()\n"
        ),
        _code(
            "# Cell 7: 3 銘柄 × MD&A センチメント比較 (pos - neg)\n"
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
