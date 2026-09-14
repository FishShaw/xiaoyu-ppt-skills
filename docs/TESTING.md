# 测试与发布机制

## 覆盖层次

| 层 | 自动检查 | 不代表什么 |
| --- | --- | --- |
| 脚本回归 | 25 个反例/正常用例：顺序、箭头、重复标签、越界路径、输出不覆盖、字体转义、共享部件保护等 | 合成 ZIP 不是合法 Office 文件样本 |
| 仓库与包装 | 元数据、链接、私密路径/常见凭据模式、可复现打包、拒绝覆盖 | 简单扫描不是完整秘密检测或脱敏认证 |
| 真实 PPT 集成 | 16:9、4:3、A4 竖版，每份 3 页；原生文字/表格/图表、合成 PNG 字节、备注、包关系、画布边界、指定链路 | 不是完整 ECMA OOXML XSD 校验 |
| 渲染与修改 | LibreOffice 实际打开；中文文本可提取；所有页生成 PNG；限定改标题时其余页像素一致 | 中文可提取不等于逐字无截断；需人工看图 |
| 人工视觉 | PR 清单要求查看全部受影响页、图标、箭头、图注与长表 | 无第二评审者时，清单完成度不是技术上不可绕过的门禁 |
| 发布 | main 精确 SHA 的 push CI 成功后，生成带清单与 SHA-256 的版本草稿 | 不自动部署/替换本地已安装 Skill |

单元测试在 Ubuntu/Windows、Python 3.11/3.13 上运行；渲染使用 Ubuntu 24.04、Noto Sans CJK SC、LibreOffice。renderer 的 apt 软件版本由 runner 提供，每次记录实际版本；不跨不同渲染环境比较像素基线。

## 本地执行

```sh
python scripts/check_repo.py
python -m unittest discover -s tests -v
npm ci --ignore-scripts
python scripts/audit_dependencies.py
# 需要 node、soffice、pdftoppm、pdftotext 和 Noto Sans CJK SC 字体
python tests/integration.py
python scripts/package_skill.py
```

首次运行前确认工具可用。`artifacts/`、`dist/` 为可再生产物，不提交 Git。重新生成使用新的干净工作目录，避免将旧预览当作新验证；打包脚本拒绝覆盖已有包。

## 分支与 PR

1. 从最新 main 创建分支；编辑代码、测试和必要文档。
2. 本地验证，通过后 push 功能分支。
3. 等待该分支最新 SHA 的 CI 成功，再创建 PR。
4. PR 触发新一轮 CI，验证与 main 的合并候选，而不只验证旧分支。
5. 下载 `presentation-evidence-<sha>`，查看 PNG/PDF/PPTX 与结果 JSON；完成视觉清单。
6. main 有新提交时更新分支，重新等待检查。只使用 PR 合并，不直接更新 main。

可使用 `python scripts/open_pr.py --title "变更说明" --body-file pr-body.md`，工具会确认工作区干净、远端分支与本地 SHA 相同，并检查该提交最近一次 push CI 成功后才创建 PR；已有 PR 时返回原链接，不重复创建。正文文件可放在工作区外，避免留下未提交文件。

CI Gate 汇总所有依赖 job，失败、取消或跳过均不算通过。无路径过滤，避免只修改文档时必需检查永久缺失。PR 使用只读 token，禁止 `pull_request_target` 执行不受信任代码。

## 保护与维护

实际设置由仓库管理员一次性应用 `.github/main-protection.json` 并回读确认；提交 JSON 本身不会改变 GitHub 设置。main 要求 PR、CI Gate、最新基线、线性历史和解决会话，禁止强推/删除，对管理员生效。默认不要求第二人批准，适合单人维护；有协作者后可提高到 1 名独立批准者。

仓库管理员仍能在设置中移除保护，GitHub Pro 不能消除这个管理权限。不得声称“任何人都绝对无法绕过”。修改门禁配置本身也走 PR，并由管理员审阅后应用。

Actions 与 npm 依赖通过 Dependabot 每周提出更新 PR；主分支每周重跑完整 CI。历史通过不保证未来依赖没有新漏洞。

## 发布与回退

CI 每次生成安装包 artifact。合并后等待 main CI 通过，再在 Actions 手动运行 `Release draft`（仅 main）；工作流检查精确 SHA 的成功 CI，生成版本草稿。人工核对后发布 GitHub Release。版本已存在时拒绝覆盖，必须通过新 PR 升版。

回退也走分支：revert 已合并变更、更新版本、完成 CI 与 PR；不 force push main，不覆盖旧 Release。全局 Skill 的本地安装由用户另行授权，避免用未合并分支覆盖稳定版本。

## 已知限制

此仓库不包含私人原型或面试文档，不提供这些素材的自动测试。原图缺字、低清晰度和裁剪并非自动被修复。复杂泳道与真正绑定节点的连接器编辑行为仍需专门样本。检查通过不等于美学满分或 Microsoft PowerPoint 全平台兼容。
