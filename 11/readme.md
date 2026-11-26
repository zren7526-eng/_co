# Jack 編譯器（nand2tetris 第 12 週作業）

用 Python 寫的 Jack 語言編譯器，把 `.jack` 原始檔編譯成 VM 指令（`.vm`），再用官方 VM Emulator 執行驗證。

## 檔案結構

```
_co/
  jack/
    jacktokenizer.py      # 詞彙分析：把 .jack 切成 token（會略過註解與空白）
    symboltable.py        # 符號表：記錄 static / field / argument / var 的型別與編號
    vmwriter.py           # 輸出 VM 指令（push、pop、call、label...）
    compilationengine.py  # 遞迴下降解析，同時直接產生 VM 指令
    jackcompiler.py       # 主程式：接受單一 .jack 檔或整個資料夾
  11/                     # 測試用的第 11 章專案
```

## 使用方式

在 `_co` 資料夾下執行：

```
python jack/jackcompiler.py 11/Seven
```

- 參數是資料夾時，會編譯裡面所有 `.jack`；是單一檔案時，只編譯該檔。
- 每個 `Xxx.jack` 會在同一個資料夾產生對應的 `Xxx.vm`。

一次編譯全部測試專案（PowerShell）：

```
foreach ($d in "Average","ComplexArrays","ConvertToBin","Pong","Seven","Square") { python jack/jackcompiler.py 11/$d }
```

## 運作流程

1. **JackTokenizer**：用正規表示式把原始碼切成 `KEYWORD`、`SYMBOL`、`IDENTIFIER`、`INT_CONST`、`STRING_CONST` 五種 token。
2. **CompilationEngine**：依 Jack 文法遞迴下降解析，每個 `compileXxx` 對應一個文法規則，邊解析邊呼叫 VMWriter 輸出指令。
3. **SymbolTable**：分「類別範圍」（static、field）與「子程式範圍」（argument、var），查詢時子程式範圍優先。
4. **VMWriter**：把符號表的 kind 對應到 VM segment（`field`→`this`、`var`→`local`、`arg`→`argument`、`static`→`static`）。

## 實作重點

- **method**：`this` 是 `argument 0`，所以先在符號表定義 `this`，函式開頭用 `push argument 0` / `pop pointer 0` 設定 `this`。
- **constructor**：用 `Memory.alloc` 依 field 數量配置記憶體，再 `pop pointer 0`。
- **運算**：`*`、`/` 呼叫 `Math.multiply`、`Math.divide`；負數用 `neg`，`true` 為 `push constant 0` 加 `not`。
- **字串常數**：`String.new` 搭配逐字元 `String.appendChar`。
- **陣列**：`a[i] = x` 先算位址（`a + i`），暫存值到 `temp 0`，再透過 `pointer 1` 與 `that 0` 存取。
- **`do` 敘述**：呼叫後 `pop temp 0` 丟掉回傳值；void 函式一律 `push constant 0` 後 `return`。
- **流程控制**：`if` 使用 `IF_FALSE{n}`、`IF_END{n}`，`while` 使用 `WHILE_EXP{n}`、`WHILE_END{n}`，編號在每個子程式內重新計算。

## 測試方式

1. 編譯專案資料夾，產生 `.vm`。
2. 開啟 nand2tetris 的 VM Emulator（2.5），**Load Program** 選整個專案資料夾。
3. Animate 設為 No animation，按 Run。

| 專案 | 預期結果 | 狀態 |
|---|---|---|
| Seven | 螢幕印出 `7` | 通過 |
| ConvertToBin | 在 RAM[8000] 放數字，RAM[8001]~[8016] 為其二進位各位元 | 通過 |
| Square | 方塊可用方向鍵移動、`z`/`x` 縮放、`q` 離開 | 通過 |
| Average | 輸入數字後印出平均值 | 通過 |
| ComplexArrays | 依序印出 5、40、0、77、110 | 通過 |
| Pong | 可玩的 Pong 遊戲 | 通過 |

## 開發環境

- Python 3.11、Windows PowerShell
- nand2tetris VM Emulator 2.5
