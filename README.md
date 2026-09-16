# xiaoyu-ppt-skills

原生可编辑、证据可追溯的 PPT 制作 Skill，附可重复运行的测试与发布流程。

## 调用

将 `skills/xiaoyu-ppt/` 安装到自己的 Codex skills 目录后：

```text
$xiaoyu-ppt 根据这些材料制作 8 页管理层汇报，16:9，保留原生图表。
$xiaoyu-ppt 只修改最新版 PPT 的第 5 页，其他页面和备注保持不变。
```

Skill 默认允许自动匹配；也支持提纲、审阅和口播任务，不会把纯文本请求强制变为 PPT。实际 PPT 构建优先使用环境中的 `pptx` 能力，缺失时说明替代工具和未覆盖检查。

## 核心原则

- 标题、文字、表格、图表和普通连接线使用原生 PPT 元素。
- Figma 只用于必要复杂图稿；真实原型优先，不重绘冒充原作。
- 按受众组织叙事，不强制 STAR、固定页数或比例。
- 区分规划、实现、验证和推断，保护用户手改版本。
- 自动几何检查与逐页视觉检查互补，不混淆验证范围。

## 开发与交付

```text
功能分支 → 本地测试 → 分支 CI → 创建 PR → PR CI + 人工看图
         → PR 合并 → main CI → 手动创建 Release 草稿 → 审阅发布
```

main 禁止直接更新；README-only 初始化是唯一经确认的例外。所有后续代码、测试和流程改动均走分支与 PR。

- [完整测试机制与操作步骤](docs/TESTING.md)
- [Skill 入口](skills/xiaoyu-ppt/SKILL.md)
- [贡献与安全约定](AGENTS.md)
- [CI 工作流](.github/workflows/ci.yml)
- [发布工作流](.github/workflows/release.yml)

仓库仅含通用源代码和合成数据，不包含私人演示稿、原型截图、简历、聊天或 Notion 内容。CI artifacts 供检查，不代表已发布版本。发布包不包含 Node 测试依赖。

许可证尚未由仓库所有者指定；公开可见不等于已授予开源许可。
