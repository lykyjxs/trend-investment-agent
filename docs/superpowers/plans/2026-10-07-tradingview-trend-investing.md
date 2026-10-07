# TradingView Trend Investing Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把仓库里的“扫地僧股票趋势投资课”蒸馏成一个可维护、可安装的 Codex skill，并在当前 Codex 任务中建立每天北京时间 08:00、完全依赖 TradingView UI 的三市场趋势选股报告。

**Architecture:** 仓库中的 `skills/tradingview-trend-investing/` 是唯一真源，包含短而可执行的 `SKILL.md`、按需加载的理论/评分/工作流参考、精选案例图、可编辑报告模板和纯计算辅助脚本。构建脚本从原始课程笔记生成完整文本参考并只复制精选图，安装脚本把真源部署到个人 Codex skills 目录。每天的 heartbeat 自动任务在同一个 Codex 任务中调用该 skill，经 TradingView 全 UI 完成筛选、图表判断和报告；不得调用其他行情源，也不得下单。

**Tech Stack:** Markdown、Python 3 标准库、PowerShell、Codex skills、Codex heartbeat automations、TradingView Web UI（Chrome/Edge，通过 computer-use）

**Spec:** `docs/superpowers/specs/2026-10-07-tradingview-trend-report-design.md`

## Global Constraints

- TradingView 是行情、筛选、指数、行业、价格与成交量的唯一数据源；任何缺失都必须显式降级或报告失败，不能去其他网站补数。
- 不执行真实下单。报告中的“条件单参考触发价”只是供用户自行确认。
- A 股以沪深 300 为环境基准；港股按行业选择恒生科技或恒生指数；美股按行业选择纳斯达克 100 或标普 500。
- 市值门槛使用各市场本币 400 亿；普通股；价格和 50/150/200 日均线满足既定多头排列。
- 观察名单是日报主体，每市场最多 10 只且评分至少 60；符合“今日新触发买点”定义的股票全部列出但只做增量报告。首次运行回看 5 个交易日，后续只报告上一交易日首次触发，依靠同一任务的历史报告去重；找不到历史报告时按首次运行处理并注明。
- 最终收缩不超过 8% 为正常，8%–12% 只能进入观察名单且必须说明降级原因，超过 12% 排除。
- 止损风险不超过 5% 为高分，5%–8% 可触发但降分，8%–12% 只能观察并标注，超过 12% 排除。
- 观察候选当前价必须位于枢纽点下方且距离不超过 8%；触发候选为最近已完成交易日首次突破枢纽点且收盘位于枢纽点上方不超过 8%。
- 压力位取最近明显摆动高点；创新高没有客观压力位时必须写“无明确压力位”，另列 2R 目标，不能把目标伪装成压力位。
- 报告只显示股票名称，不显示股票代码。
- 每个实现任务都先运行指定失败测试，再实现最小改动使其通过；不得用人工浏览替代可自动化的契约测试。
- 每完成一个任务立即提交一次小型 Git commit。仅在最终全量验证通过后推送远端。

## Target File Map

```text
automation/
└── daily-trend-report-prompt.md
docs/superpowers/
├── plans/2026-10-07-tradingview-trend-investing.md
└── specs/2026-10-07-tradingview-trend-report-design.md
evals/tradingview-trend-investing/
├── baseline-results.md
├── scenarios.md
├── tradingview-smoke-test.md
└── with-skill-results.md
skills/tradingview-trend-investing/
├── SKILL.md
├── agents/openai.yaml
├── assets/
│   ├── daily-report-template.md
│   ├── data-failure-template.md
│   └── no-new-data-template.md
├── references/
│   ├── casebook.md
│   ├── course-notes.md
│   ├── images/                       # 只放精选案例图
│   ├── scoring-rubric.md
│   ├── strategy-rules.md
│   └── tradingview-workflow.md
└── scripts/
    └── calculate_trade_metrics.py
tests/
├── test_build_skill_references.py
├── test_calculate_trade_metrics.py
└── test_skill_package.py
tools/
├── build_skill_references.py
└── install-tradingview-trend-skill.ps1
```

## Review Focus

后续独立审查必须重点尝试击穿以下五个最容易“表面正确、实际出错”的边界：

1. **8%/12% 边界和方向：** 观察候选必须在枢纽下方，触发候选必须在枢纽上方；8.00% 和 12.00% 的包含关系要与设计一致。
2. **增量去重：** 首次回看 5 个交易日，之后只报上一交易日首次触发；不能因自动任务重复运行而重复推送旧信号。
3. **无压力位情形：** 创新高只能报告“无明确压力位 + 2R 目标”，不能把计算目标说成市场真实压力。
4. **行业与大盘映射：** 港股科技/非科技、美股科技/非科技必须选对环境指数；大盘非第二阶段时要保留事实但降低建议强度。
5. **数据失败隔离：** 单一市场或字段失败时只能标注 TradingView 数据不可得；不能混用旧数据或外部网站，也不能让一个市场的失败吞掉其他市场的正常结果。

---

## Task 1: 建立 skill 行为基线（RED）

**Files:**

- Create: `evals/tradingview-trend-investing/scenarios.md`
- Create: `evals/tradingview-trend-investing/baseline-results.md`
- Reference: `docs/superpowers/specs/2026-10-07-tradingview-trend-report-design.md`

- [ ] **Step 1: 写六个压力场景**

  在 `scenarios.md` 中定义固定输入和通过条件：

  1. 价格位于枢纽下方 7.9%，最终收缩 7.9%，风险 4.8%，应进入观察名单。
  2. 价格位于枢纽下方 6%，最终收缩 9.5%，应进入观察名单并注明“因最终收缩 8%–12% 降级”。
  3. 上一交易日首次突破枢纽 4%，风险 7%，压力收益只有 1.4R，应全部列入已触发并警告“不建议追入”。
  4. 创新高无压力位，应显示 2R 目标且明确不是压力位。
  5. 港股科技股与美股非科技股，应分别选择恒生科技和标普 500。
  6. A 股 TradingView 行业字段不可得、港美股正常，应只降级 A 股且禁止外部补数。

- [ ] **Step 2: 在没有新 skill 的上下文中运行独立 agent 测试**

  按 `superpowers:writing-skills/references/testing-skills-with-subagents.md` 的流程，把每个场景交给一个不知道本计划内容的独立 agent。只提供场景，不提供拟建 skill。

- [ ] **Step 3: 记录基线失败证据**

  `baseline-results.md` 必须逐场景记录：agent 输出摘要、是否通过、具体误判、后来 skill 需要补上的规则。预期至少观察到边界、压力位标签、增量去重或数据源隔离中的一种失败；若全部通过，增加一个更有诱惑力的组合场景后重测，不能伪造 RED。

- [ ] **Step 4: 提交基线**

  ```powershell
  git add evals/tradingview-trend-investing
  git commit -m "test: capture trend skill behavior baseline"
  ```

---

## Task 2: 搭建标准 skill 骨架与包契约

**Files:**

- Create: `skills/tradingview-trend-investing/SKILL.md`
- Create: `skills/tradingview-trend-investing/agents/openai.yaml`
- Create: `skills/tradingview-trend-investing/assets/`
- Create: `skills/tradingview-trend-investing/references/`
- Create: `skills/tradingview-trend-investing/scripts/`
- Create: `tests/test_skill_package.py`

- [ ] **Step 1: 先写失败的结构测试**

  `tests/test_skill_package.py` 使用 `unittest`，至少断言：

  ```python
  REQUIRED = {
      "SKILL.md",
      "agents/openai.yaml",
      "assets/daily-report-template.md",
      "assets/no-new-data-template.md",
      "assets/data-failure-template.md",
      "references/course-notes.md",
      "references/strategy-rules.md",
      "references/scoring-rubric.md",
      "references/tradingview-workflow.md",
      "references/casebook.md",
      "scripts/calculate_trade_metrics.py",
  }
  ```

  另断言 `SKILL.md` 的 frontmatter 只含允许字段、不含 TODO，`openai.yaml` 的默认提示明确写 `$tradingview-trend-investing`。

- [ ] **Step 2: 运行测试并确认因目录缺失失败**

  ```powershell
  python -m unittest tests.test_skill_package -v
  ```

  Expected: `skills/tradingview-trend-investing` 或必需文件不存在。

- [ ] **Step 3: 用官方初始化脚本创建骨架**

  ```powershell
  python C:\Users\YangkeLan\.codex\skills\.system\skill-creator\scripts\init_skill.py tradingview-trend-investing --path skills --resources scripts,references,assets --interface display_name="TradingView 趋势投资" --interface short_description="用扫地僧趋势体系生成三市场买点日报" --interface default_prompt="Use $tradingview-trend-investing to generate today's TradingView-only trend investing report."
  ```

  不使用 `--examples`，避免保留占位资源。

- [ ] **Step 4: 写最小可发现元数据**

  `SKILL.md` 的 description 要同时说明“做什么”和“何时触发”，包括 TradingView、A/港/美股、趋势/VCP、买点观察、每日复盘等关键词。`agents/openai.yaml` 保持 `allow_implicit_invocation: true`，不声明不存在的 MCP 依赖。

- [ ] **Step 5: 运行官方校验并保留预期的资源缺失失败**

  ```powershell
  python C:\Users\YangkeLan\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tradingview-trend-investing
  python -m unittest tests.test_skill_package -v
  ```

  Expected: 官方 frontmatter 校验通过；包契约仍因后续资源尚未创建而失败。

- [ ] **Step 6: 提交骨架与 RED 契约**

  ```powershell
  git add skills/tradingview-trend-investing tests/test_skill_package.py
  git commit -m "test: define trend skill package contract"
  ```

---

## Task 3: 以 TDD 实现交易指标纯计算脚本

**Files:**

- Create: `tests/test_calculate_trade_metrics.py`
- Create: `skills/tradingview-trend-investing/scripts/calculate_trade_metrics.py`
- Modify: `tests/test_skill_package.py`

- [ ] **Step 1: 写失败的边界测试**

  用 `importlib.util` 从 skill 目录加载脚本。目标接口：

  ```python
  def calculate_metrics(
      current_price: float,
      pivot_price: float,
      support_price: float,
      pressure_price: float | None = None,
  ) -> dict[str, float | None]: ...

  def classify_band(value: float, normal_max: float = 8.0,
                    watch_max: float = 12.0) -> str: ...
  ```

  测试至少覆盖：枢纽距离带正负号、预期亏损%、预期盈利%、R 倍数、无压力位的 2R 目标、零/负价格拒绝、`8.0 -> normal`、`8.01 -> watch`、`12.0 -> watch`、`12.01 -> exclude`。

- [ ] **Step 2: 运行并确认缺少实现**

  ```powershell
  python -m unittest tests.test_calculate_trade_metrics -v
  ```

  Expected: 模块或函数不存在。

- [ ] **Step 3: 写最小实现和 CLI**

  百分比统一按当前价作为分母：

  ```python
  pivot_distance_pct = (current_price - pivot_price) / pivot_price * 100
  potential_loss_pct = (current_price - support_price) / current_price * 100
  potential_gain_pct = (pressure_price - current_price) / current_price * 100
  reward_risk = potential_gain_pct / potential_loss_pct
  two_r_target = current_price + 2 * (current_price - support_price)
  ```

  CLI 接收 JSON 字符串并输出 JSON，便于 agent 遇到密集计算时调用；所有结果保留未舍入原值，由显示层决定小数位。

- [ ] **Step 4: 运行单元测试**

  ```powershell
  python -m unittest tests.test_calculate_trade_metrics -v
  ```

  Expected: 全部通过。

- [ ] **Step 5: 提交**

  ```powershell
  git add skills/tradingview-trend-investing/scripts/calculate_trade_metrics.py tests
  git commit -m "feat: add trend trade metric calculator"
  ```

---

## Task 4: 可重复生成完整课程参考与精选图片

**Files:**

- Create: `tools/build_skill_references.py`
- Create: `tests/test_build_skill_references.py`
- Create: `skills/tradingview-trend-investing/references/course-notes.md`
- Create: `skills/tradingview-trend-investing/references/images/*.png`
- Source: `trend-investment.md`
- Source: `trend-investment-images/*.png`

- [ ] **Step 1: 为构建器写失败测试**

  测试临时目录中的最小笔记，断言：

  - 文本、标题和案例名完整保留；
  - 精选 Obsidian 图片 `![[Pasted image X.png]]` 变为 `![案例图](images/Pasted%20image%20X.png)`；
  - 未精选图片变成 `> 原图文件：Pasted image Y.png（未随 skill 打包）`；
  - 精选源图不存在时构建失败；
  - 生成目录中没有未列入清单的图片。

- [ ] **Step 2: 运行并确认失败**

  ```powershell
  python -m unittest tests.test_build_skill_references -v
  ```

  Expected: `tools.build_skill_references` 不存在。

- [ ] **Step 3: 实现确定性构建器**

  公开接口：

  ```python
  def build_course_reference(
      source_note: Path,
      source_images: Path,
      destination: Path,
      selected_images: tuple[str, ...],
  ) -> None: ...
  ```

  默认精选清单使用以下 24 张源图（文件名保留原样，避免案例映射失真）：

  ```text
  Pasted image 20250502095312.png
  Pasted image 20250502100531.png
  Pasted image 20250502102252.png
  Pasted image 20250502104354.png
  Pasted image 20250502110035.png
  Pasted image 20250509202043.png
  Pasted image 20250509213405.png
  Pasted image 20250509215610.png
  Pasted image 20250510095552.png
  Pasted image 20250510184348.png
  Pasted image 20250510184327.png
  Pasted image 20250510184738.png
  Pasted image 20250513213300.png
  Pasted image 20250513213658.png
  Pasted image 20250513214157.png
  Pasted image 20250513220140.png
  Pasted image 20250513223236.png
  Pasted image 20251004223449.png
  Pasted image 20251004223901.png
  Pasted image 20251004223820.png
  Pasted image 20251004224138.png
  Pasted image 20251004224754.png
  Pasted image 20251002164239.png
  Pasted image 20251006165059.png
  ```

- [ ] **Step 4: 生成真实参考文件并校验规模**

  ```powershell
  python tools/build_skill_references.py
  python -m unittest tests.test_build_skill_references tests.test_skill_package -v
  ```

  Expected: `course-notes.md` 保留完整课程正文；`references/images/` 恰好 24 张，不能意外复制 168 张全部截图。

- [ ] **Step 5: 提交**

  ```powershell
  git add tools/build_skill_references.py tests skills/tradingview-trend-investing/references/course-notes.md skills/tradingview-trend-investing/references/images
  git commit -m "feat: build course reference and selected case images"
  ```

---

## Task 5: 编写核心工作流与评分参考

**Files:**

- Modify: `skills/tradingview-trend-investing/SKILL.md`
- Create: `skills/tradingview-trend-investing/references/strategy-rules.md`
- Create: `skills/tradingview-trend-investing/references/scoring-rubric.md`
- Create: `skills/tradingview-trend-investing/references/tradingview-workflow.md`
- Modify: `tests/test_skill_package.py`

- [ ] **Step 1: 扩展失败契约测试**

  断言包内明确出现且只出现一套规范数值：本币 400 亿、观察距离 8%、最终收缩 8/12%、风险 5/8/12%、评分 15/20/10/15/20/20、观察分档 80/70/60、每市场最多 10、首次 5 个交易日、后续上一交易日。

  另断言：

  - 成交量/相对成交量是状态字段，不参与总分；
  - 报告禁止外部行情源和自动下单；
  - 行业指数映射四分支完整；
  - `SKILL.md` 采用按需读取，不把完整课程重复粘贴到主文件。

- [ ] **Step 2: 运行测试并确认缺少规则而失败**

  ```powershell
  python -m unittest tests.test_skill_package -v
  ```

- [ ] **Step 3: 写 `strategy-rules.md`**

  覆盖 Stage 1–4、Stage 2 最小判定、趋势模板、VCP、枢纽点、最终收缩、支撑/止损、压力/2R、观察与触发的互斥关系、市场环境降级规则和禁止追涨条件。对“个股第二阶段”和“均线多头排列”说明：前者是阶段结论，后者是可观测趋势证据，评分时分别评估但避免重复使用同一证据。

- [ ] **Step 4: 写 `scoring-rubric.md`**

  固定 100 分：市场环境 15、个股第二阶段趋势模板 20、相对强弱与行业地位 10、VCP 整体 15、最终收缩 20、止损与风险收益 20。逐项写满分、部分分和 0 分锚点，并明确硬性排除优先于总分。

- [ ] **Step 5: 写 `tradingview-workflow.md`**

  明确周度全量流程与每日增量流程：打开股票筛选器、分别切换 CN/HK/US、设置普通股/本币市值/均线条件、读取行业和相对成交量、在图表查看指数与个股日线、识别枢纽/支撑/压力、使用同任务上次报告去重。写出 UI 变化时按标签语义寻找控件、不得用屏幕坐标硬编码。

- [ ] **Step 6: 完成短主指令 `SKILL.md`**

  主文件控制在日常可加载范围，只包含触发条件、不可违反的边界、执行顺序、按情形读取哪些 reference/template、计算脚本调用方法、失败处理和最终检查表。

- [ ] **Step 7: 验证**

  ```powershell
  python C:\Users\YangkeLan\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tradingview-trend-investing
  python -m unittest tests.test_skill_package -v
  ```

  Expected: frontmatter 与规则契约通过；只可能因模板/案例尚未完成而失败。

- [ ] **Step 8: 提交**

  ```powershell
  git add skills/tradingview-trend-investing tests/test_skill_package.py
  git commit -m "feat: encode trend strategy and TradingView workflow"
  ```

---

## Task 6: 编写案例库和三套可编辑模板

**Files:**

- Create: `skills/tradingview-trend-investing/references/casebook.md`
- Create: `skills/tradingview-trend-investing/assets/daily-report-template.md`
- Create: `skills/tradingview-trend-investing/assets/no-new-data-template.md`
- Create: `skills/tradingview-trend-investing/assets/data-failure-template.md`
- Modify: `tests/test_skill_package.py`

- [ ] **Step 1: 先扩展失败测试**

  日报模板必须包含“市场摘要”“接近买点观察名单（主体）”“上一交易日新触发买点（次要）”“异常与缺失”四部分。每只股票的条目必须含：名称、行业、现价、枢纽、距离、条件单参考触发价、支撑/止损/亏损%、压力或 2R/盈利%/R 倍数、最终收缩、评分、优势、缺口、风险和降级说明。

  测试还要禁止股票条目出现“股票代码/代码”字段，并检查观察每市场最多 10、触发项不设数量上限。

- [ ] **Step 2: 运行并确认模板缺失失败**

  ```powershell
  python -m unittest tests.test_skill_package -v
  ```

- [ ] **Step 3: 写 `casebook.md`**

  从课程原文提炼 NVIDIA、腾讯、捷蓝航空、eBay、DICK'S Sporting Goods、小米，以及移动止损/加仓案例。每个案例都写“背景—图形证据—正确判断—常见误判—对应规则—图例链接”，不把历史案例当作实时推荐。

- [ ] **Step 4: 写日报模板**

  观察名单排在触发清单前。评分显示为 `总分/100（高优先级|普通|低优先级）`。所有百分比明确正负含义。8%–12% 最终收缩和 8%–12% 风险必须分别有固定醒目标记。

- [ ] **Step 5: 写无新数据与失败模板**

  - `no-new-data-template.md`：三个市场都没有新的已完成交易日数据时只发简短说明，不复读旧名单。
  - `data-failure-template.md`：区分 TradingView 未登录、页面不可达、筛选器字段缺失、单市场数据失败和全部失败；保留已成功市场的结果。

- [ ] **Step 6: 全量测试**

  ```powershell
  python -m unittest discover -s tests -p "test_*.py" -v
  python C:\Users\YangkeLan\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tradingview-trend-investing
  ```

  Expected: 全部通过，skill 包结构完整。

- [ ] **Step 7: 提交**

  ```powershell
  git add skills/tradingview-trend-investing tests/test_skill_package.py
  git commit -m "feat: add trend casebook and report templates"
  ```

---

## Task 7: 用独立 agent 做 GREEN 与回归压力测试

**Files:**

- Create: `evals/tradingview-trend-investing/with-skill-results.md`
- Modify as needed: `skills/tradingview-trend-investing/**`
- Modify as needed: `tests/**`

- [ ] **Step 1: 对同一组六个场景启用新 skill 重测**

  每个测试 agent 只得到场景、skill 路径和允许读取的资源，不得到预期实现细节。使用和基线相同的评分表，保证前后可比。

- [ ] **Step 2: 增加五个审查焦点的对抗变体**

  至少覆盖精确 8.00/12.00 边界、历史报告已含同一突破、科技行业映射歧义、创新高无压力、TradingView 部分字段卡死。

- [ ] **Step 3: 记录结果并修补最小规则**

  `with-skill-results.md` 逐项链接到 `baseline-results.md`，写明从失败到通过的变化。若 agent 仍能合理误解，先补测试再改 skill；禁止只在结果文档里解释。

- [ ] **Step 4: 运行所有自动化验证**

  ```powershell
  python -m unittest discover -s tests -p "test_*.py" -v
  python C:\Users\YangkeLan\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tradingview-trend-investing
  ```

- [ ] **Step 5: 提交**

  ```powershell
  git add evals skills tests
  git commit -m "test: verify trend skill under pressure scenarios"
  ```

---

## Task 8: 安装为个人 Codex skill 并验证可发现性

**Files:**

- Create: `tools/install-tradingview-trend-skill.ps1`
- Modify: `tests/test_skill_package.py`
- Deploy: `C:\Users\YangkeLan\.codex\skills\tradingview-trend-investing\**`

- [ ] **Step 1: 写安全安装脚本契约测试**

  检查脚本只允许源目录 `skills/tradingview-trend-investing` 和目标叶目录 `tradingview-trend-investing`，拒绝把目标解析为 `.codex\skills` 根目录或更宽路径；复制完成后逐文件比较 SHA-256，并报告源中存在但目标缺失/内容不一致的文件。

- [ ] **Step 2: 实现安装脚本**

  脚本参数：

  ```powershell
  param(
    [string]$Source = "skills/tradingview-trend-investing",
    [string]$Destination = "C:\Users\YangkeLan\.codex\skills\tradingview-trend-investing"
  )
  ```

  不删除目标目录，不对 `.codex\skills` 做递归清理；只创建缺失目录、覆盖同名 skill 文件并校验哈希，避免影响用户其他 skills。

- [ ] **Step 3: 在临时目标测试，再安装到真实个人目录**

  ```powershell
  $testDestination = Join-Path $env:TEMP 'tradingview-trend-investing-install-test'
  powershell -NoProfile -File tools/install-tradingview-trend-skill.ps1 -Destination $testDestination
  powershell -NoProfile -File tools/install-tradingview-trend-skill.ps1
  ```

  测试目标必须是明确叶目录；若已存在，使用另一个新临时叶目录，不执行递归删除。

- [ ] **Step 4: 校验仓库源与安装副本**

  ```powershell
  python C:\Users\YangkeLan\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tradingview-trend-investing
  python C:\Users\YangkeLan\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\YangkeLan\.codex\skills\tradingview-trend-investing
  ```

  Expected: 两份都显示 `Skill is valid!`，安装脚本哈希校验通过。

- [ ] **Step 5: 提交安装器**

  ```powershell
  git add tools/install-tradingview-trend-skill.ps1 tests/test_skill_package.py
  git commit -m "feat: add safe personal skill installer"
  ```

---

## Task 9: TradingView 全 UI 三市场冒烟测试

**Files:**

- Create: `evals/tradingview-trend-investing/tradingview-smoke-test.md`
- Modify as needed: `skills/tradingview-trend-investing/references/tradingview-workflow.md`

- [ ] **Step 1: 使用 computer-use 打开用户本地 TradingView**

  仅操控浏览器 UI。确认登录状态、股票筛选器、K 线图、行业字段、成交量和相对成交量字段可见。若因登录/订阅/市场权限受阻，截图或记录可见错误，不访问替代行情站。

- [ ] **Step 2: 逐市场验证初筛**

  对 CN、HK、US 分别验证：普通股、本币市值大于 400 亿、价格 > SMA50、SMA50 > SMA150、SMA150 > SMA200。记录 TradingView 实际字段中文/英文名称以及 UI 差异。

- [ ] **Step 3: 各抽一只候选完成图表检查**

  不要求它一定入选，重点验证能从 TradingView UI 获取日报所需字段：公司名称、行业、现价、均线、枢纽、支撑、压力、成交量/相对成交量，以及正确的环境指数。

- [ ] **Step 4: 验证周度与每日路径**

  周度路径重新确认三市场筛选条件；每日路径复用筛选器并只检查新完成交易日。记录页面刷新、筛选器保存状态或 UI 不稳定点。

- [ ] **Step 5: 写冒烟测试记录并修正规则**

  `tradingview-smoke-test.md` 包含日期、浏览器、每市场结果、阻塞点和是否需要人工登录。若 UI 标签与 reference 不一致，只更新语义定位说明，不写死坐标。

- [ ] **Step 6: 回归并提交**

  ```powershell
  python -m unittest discover -s tests -p "test_*.py" -v
  git add evals/tradingview-trend-investing/tradingview-smoke-test.md skills/tradingview-trend-investing/references/tradingview-workflow.md
  git commit -m "test: verify TradingView-only market workflow"
  ```

---

## Task 10: 创建每天 08:00 的当前任务 heartbeat

**Files:**

- Create: `automation/daily-trend-report-prompt.md`
- External state: Codex heartbeat automation attached to current task

- [ ] **Step 1: 写版本化的自动任务提示词**

  提示词必须自然、完整且用户可读，明确：

  - 调用 `$tradingview-trend-investing`；
  - 使用本地 TradingView 全 UI 且只能使用 TradingView 行情；
  - 先检查是否有新的已完成交易日数据；
  - 观察名单为主、每市场最多 10；新触发全部列出；
  - 从同一任务最近一次报告判断首次/增量和去重；
  - 不显示股票代码，不下单；
  - 无新数据时使用短模板；部分失败时保留成功市场并用失败模板说明。

- [ ] **Step 2: 创建 heartbeat automation**

  使用 Codex `automation_update`，配置：

  - Kind: `heartbeat`
  - Destination: current thread
  - Name: `每日 TradingView 趋势选股`
  - Schedule: 每天 08:00，时区 `Asia/Shanghai`
  - Status: `ACTIVE`
  - Notification policy: 默认，仅在报告、失败或需要用户动作时通知；不要额外发送无意义的运行状态更新。

  按 `automation_update` 的 schema 填写时区化日程；不要把调度指令写进 prompt，也不要向用户展示原始 RRULE。

- [ ] **Step 3: 读取 automation 验证**

  再调用 `automation_update` 的 `view` 模式，核对名称、当前任务目标、Asia/Shanghai 的 08:00、ACTIVE 和完整 prompt。若工具把时区归一化，按返回的下一次运行时间交叉验证北京时间。

- [ ] **Step 4: 提交提示词**

  ```powershell
  git add automation/daily-trend-report-prompt.md
  git commit -m "feat: define daily trend report automation prompt"
  ```

---

## Task 11: 最终审查、安装同步与推送

**Files:**

- Review: all files above
- Deploy: `C:\Users\YangkeLan\.codex\skills\tradingview-trend-investing\**`
- External state: active heartbeat automation

- [ ] **Step 1: 使用 `superpowers:verification-before-completion`**

  不能根据之前的测试结果宣称完成，必须重新运行：

  ```powershell
  python tools/build_skill_references.py
  python -m unittest discover -s tests -p "test_*.py" -v
  python C:\Users\YangkeLan\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/tradingview-trend-investing
  powershell -NoProfile -File tools/install-tradingview-trend-skill.ps1
  python C:\Users\YangkeLan\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\YangkeLan\.codex\skills\tradingview-trend-investing
  git diff --check
  git status --short
  ```

  Expected: 测试全部通过、两份 skill 均有效、安装哈希一致、无 whitespace 错误、只有预期变更。

- [ ] **Step 2: 请求独立最终审查**

  使用 `superpowers:requesting-code-review`，要求审查者逐条对照设计稿、Global Constraints 和 Review Focus，尤其检查是否偷偷引入非 TradingView 来源、是否把观察与触发混在一起、是否有显示股票代码的模板字段。

- [ ] **Step 3: 修复审查问题并再次运行完整验证**

  每个修复先补回归测试，再改实现。若修改了 skill 源，重新运行安装器同步个人副本。

- [ ] **Step 4: 检查 automation 最终状态**

  用 `automation_update` 的 `view` 模式确认任务仍为 ACTIVE 且下一次运行时间正确；无需提前强制执行真实日报，除非用户要求立即试跑。

- [ ] **Step 5: 提交最终修复并推送个人仓库**

  ```powershell
  git add .
  git commit -m "chore: finalize TradingView trend investing skill"
  git push origin main
  ```

  若没有最终修复导致工作树为空，跳过空 commit，但仍执行 `git push origin main`。

- [ ] **Step 6: 向用户交付**

  最终说明应包含：skill 仓库位置、个人安装位置、如何手动调用 `$tradingview-trend-investing`、自动任务名称与下次运行时间、测试结果、TradingView 登录或订阅限制（如有）、以及报告不构成投资建议且不会自动下单。
