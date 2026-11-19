# Nand2Tetris 第 7、8 章：VM Translator

用 Python 實作 VM translator，把 `.vm`（VM 指令）翻譯成 Hack 組合語言 `.asm`。
第 7 章是基本版（算術與記憶體存取），第 8 章在其上擴充（流程控制與函式呼叫）。

## 專案結構

```
_co/
├── 07/   MemoryAccess、StackArithmetic 測試檔
├── 08/   FunctionCalls、ProgramFlow 測試檔
│   └── vmtranslator.py   ← translator 主程式
```

## 支援的指令

| 類別 | 指令 |
|---|---|
| 算術與邏輯 | `add` `sub` `neg` `and` `or` `not` `eq` `gt` `lt` |
| 記憶體存取 | `push` / `pop`：`constant` `local` `argument` `this` `that` `temp` `pointer` `static` |
| 流程控制 | `label` `goto` `if-goto` |
| 函式 | `function` `call` `return` |
| 其他 | bootstrap（`SP=256`、`call Sys.init`）、資料夾輸入（多個 `.vm` 合併成一個 `.asm`） |

## 程式結構

- **`parse()`**：讀 `.vm`，去掉註解與空白行，切成指令。
- **`CodeWriter`**：把每個指令翻成 Hack 組合語言。
  - 比較指令用計數器產生不重複標籤（`TRUE_n`、`END_n`）。
  - `call` 的返回標籤為 `函式名$ret.n`。
  - `label` / `goto` / `if-goto` 的標籤為 `函式名$標籤`。
  - `static i` 翻成 `檔名.i`。
- **`main()`**：接收單一 `.vm` 或資料夾；資料夾內有 `Sys.vm` 時自動加上 bootstrap。

## 使用方式

在 `08` 資料夾執行（PowerShell）：

```powershell
# 單一檔案
python vmtranslator.py "ProgramFlow\BasicLoop\BasicLoop.vm"

# 資料夾（多檔案，會自動加 bootstrap）
python vmtranslator.py "FunctionCalls\FibonacciElement"

# 不加 bootstrap（SimpleFunction、NestedCall 需要）
python vmtranslator.py "FunctionCalls\SimpleFunction\SimpleFunction.vm" --no-init
```

輸出的 `.asm` 會放在 `.vm`（或資料夾）旁邊。

## 驗證流程

1. 用 translator 產生 `.asm`
2. 開啟桌面版 `CPUEmulator.bat`
3. Load Script 選對應的 `.tst`，速度調到 Fast、Animate 設為 No animation，按 `>>`
4. 底部顯示 `End of script - Comparison ended successfully` 即通過
5. 失敗時比對 `.out` 與 `.cmp`，找出不同的位址

## 測試進度

**第 7 章**
- [ ] SimpleAdd
- [ ] StackTest
- [ ] BasicTest
- [ ] PointerTest
- [ ] StaticTest

**第 8 章**
- [x] BasicLoop
- [ ] FibonacciSeries
- [ ] SimpleFunction
- [ ] NestedCall
- [ ] FibonacciElement
- [ ] StaticsTest

## 開發環境

- Python 3、VS Code、PowerShell
- Nand2Tetris Software Suite 2.7（桌面版：CPUEmulator、VMEmulator）

## 注意事項

- `.out` 是測試輸出，不需要進 Git，建議加進 `.gitignore`。
- SimpleFunction、NestedCall 的 `.tst` 會自己設定 RAM，要加 `--no-init`。
- `.tst` 要在對應資料夾載入，`.asm`、`.tst`、`.cmp` 需在同一個位置。