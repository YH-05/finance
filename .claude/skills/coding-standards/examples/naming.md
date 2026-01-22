# 命名規則詳細例

変数・関数・クラス・定数の命名パターン集です。

## 命名規則サマリー

| 対象 | 規則 | 例 |
|------|------|-----|
| 変数 | snake_case | `user_name`, `task_count` |
| 関数 | snake_case（動詞） | `get_user()`, `calculate_total()` |
| クラス | PascalCase（名詞） | `UserService`, `TaskRepository` |
| 定数 | UPPER_SNAKE | `MAX_RETRY_COUNT`, `API_URL` |
| モジュール | snake_case | `user_service.py` |
| プライベート | _prefix | `_internal_method()` |

## 変数の命名

### 基本パターン

```python
# 名詞を使用
user_name = "John"
task_list = []
order_total = 0.0
error_count = 0

# 複数形は list/set/dict を示唆
users = [user1, user2]
task_ids = {"id1", "id2"}
user_map = {"id1": user1}

# 単数形は単一オブジェクト
user = get_user(user_id)
task = create_task(data)
```

### Boolean 変数

```python
# is_ : 状態を表す
is_valid = True
is_completed = False
is_active = True
is_empty = len(items) == 0

# has_ : 所有・存在を表す
has_permission = True
has_error = False
has_children = len(children) > 0

# should_ : 推奨・期待を表す
should_retry = True
should_validate = False
should_log = True

# can_ : 能力・可能性を表す
can_delete = user.has_permission("delete")
can_edit = True

# 動詞の過去分詞
loaded = True
initialized = False
processed = True
```

### コレクション変数

```python
# リスト: 複数形
users = []
task_items = []
selected_ids = []

# 辞書: _map, _dict, _by_
user_map = {}
task_by_id = {}
config_dict = {}
users_by_email = {}

# セット: _set, 複数形
unique_ids = set()
valid_statuses = {"active", "pending"}
processed_items = set()
```

### 一時変数

```python
# ループ変数
for user in users:
    ...

for i, item in enumerate(items):
    ...

for key, value in data.items():
    ...

# 内包表記
squared = [x * x for x in numbers]
filtered = [item for item in items if item.is_valid]

# 短い変数名が許容されるケース
# - ループカウンタ: i, j, k
# - 座標: x, y, z
# - 数学的変数: n, m
# - 一時的なイテレータ: item, elem
```

## 関数の命名

### 動詞で始める

```python
# データ取得
def get_user(user_id: str) -> User: ...
def fetch_data(url: str) -> dict: ...
def load_config(path: str) -> Config: ...
def read_file(path: str) -> str: ...

# データ作成
def create_task(data: TaskData) -> Task: ...
def build_query(params: dict) -> str: ...
def generate_report(data: list) -> Report: ...
def make_request(url: str) -> Request: ...

# データ更新
def update_user(user_id: str, data: dict) -> User: ...
def set_status(task: Task, status: str) -> None: ...
def modify_config(key: str, value: str) -> None: ...

# データ削除
def delete_task(task_id: str) -> None: ...
def remove_item(item: Item) -> None: ...
def clear_cache() -> None: ...

# 検証
def validate_email(email: str) -> bool: ...
def check_permission(user: User, action: str) -> bool: ...
def verify_token(token: str) -> bool: ...
def is_valid_input(data: dict) -> bool: ...

# 変換
def convert_to_json(data: object) -> str: ...
def parse_date(date_str: str) -> datetime: ...
def format_currency(amount: float) -> str: ...
def transform_data(raw: dict) -> ProcessedData: ...

# 計算
def calculate_total(items: list) -> float: ...
def compute_hash(data: bytes) -> str: ...
def count_items(collection: list) -> int: ...

# 検索
def find_user(email: str) -> User | None: ...
def search_tasks(query: str) -> list[Task]: ...
def filter_items(items: list, predicate: Callable) -> list: ...
```

### Boolean を返す関数

```python
# is_ で始める
def is_valid(data: dict) -> bool: ...
def is_empty(collection: list) -> bool: ...
def is_authenticated(user: User) -> bool: ...

# has_ で始める
def has_permission(user: User, action: str) -> bool: ...
def has_error(response: Response) -> bool: ...

# can_ で始める
def can_access(user: User, resource: Resource) -> bool: ...
def can_delete(user: User, item: Item) -> bool: ...

# should_ で始める
def should_retry(error: Exception) -> bool: ...
def should_cache(response: Response) -> bool: ...
```

### 非同期関数

```python
# 通常の命名に async を追加しない
# 関数名は同期版と同じでよい
async def fetch_user(user_id: str) -> User: ...
async def save_task(task: Task) -> None: ...
async def process_batch(items: list) -> list: ...
```

## クラスの命名

### 基本パターン

```python
# サービスクラス
class UserService: ...
class TaskManager: ...
class OrderProcessor: ...

# リポジトリ/データアクセス
class UserRepository: ...
class TaskStore: ...
class ConfigLoader: ...

# ファクトリ
class UserFactory: ...
class TaskBuilder: ...

# ハンドラ
class RequestHandler: ...
class EventHandler: ...
class ErrorHandler: ...

# バリデータ
class EmailValidator: ...
class InputValidator: ...

# コンバータ/フォーマッタ
class DateConverter: ...
class CurrencyFormatter: ...
class JsonSerializer: ...
```

### 抽象クラス/基底クラス

```python
# Base または Abstract プレフィックス
class BaseRepository: ...
class AbstractHandler: ...

# または Interface サフィックス（Protocol の場合）
class RepositoryInterface(Protocol): ...
```

### データクラス

```python
from dataclasses import dataclass

# 単純な名詞
@dataclass
class User: ...

@dataclass
class Task: ...

@dataclass
class Order: ...

# Config/Options/Settings サフィックス
@dataclass
class DatabaseConfig: ...

@dataclass
class RetryOptions: ...

@dataclass
class AppSettings: ...

# Request/Response サフィックス
@dataclass
class CreateTaskRequest: ...

@dataclass
class UserResponse: ...

# Result/Error サフィックス
@dataclass
class ValidationResult: ...

@dataclass
class ProcessingError: ...
```

## 定数の命名

```python
# 設定値
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
BUFFER_SIZE = 4096

# URL/パス
API_BASE_URL = "https://api.example.com"
CONFIG_FILE_PATH = "/etc/myapp/config.yaml"

# 状態/ステータス
STATUS_PENDING = "pending"
STATUS_COMPLETED = "completed"

# または Enum を使用（推奨）
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
```

## 略語の扱い

```python
# 一般的な略語は大文字のまま
http_client = HttpClient()  # ではなく HTTPClient
url_parser = UrlParser()    # ではなく URLParser
json_data = JsonData()      # ではなく JSONData

# ただし定数では元の形式を維持
API_URL = "https://..."     # api_url ではない
HTTP_TIMEOUT = 30           # http_timeout ではない

# 2文字の略語は両方大文字
io_error = IOError()
db_connection = DBConnection()

# 複合語での扱い
get_http_response()         # get_HTTP_response ではない
parse_json_data()           # parse_JSON_data ではない
```

## アンチパターン

### 避けるべき命名

```python
# 曖昧な名前
data = ...          # 何のデータ？
temp = ...          # 何の一時データ？
info = ...          # 何の情報？
result = ...        # 処理の結果を明確に

# 型名をそのまま使う
list = []           # 組み込み型を上書き
dict = {}           # 代わりに items, mapping など

# 意味のない接頭辞/接尾辞
my_user = ...       # my は不要
user_obj = ...      # obj は不要
str_name = ...      # str は不要（型ヒントで明確）

# 過度に長い名前
get_user_by_email_address_and_return_user_object = ...
# → get_user_by_email

# 略語の乱用
usr = ...           # user
cnt = ...           # count
btn = ...           # button
```

### 改善例

```python
# Before
d = fetch_data()
process(d)
r = d["result"]

# After
user_data = fetch_user_data()
processed_data = process_user_data(user_data)
active_users = processed_data["active_users"]
```
