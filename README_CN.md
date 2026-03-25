# Agentic Commerce Skills

[English](README.md) | 中文

帮助商家接入 [UCP（Universal Commerce Protocol）](https://github.com/Universal-Commerce-Protocol/ucp)的 AI Agent 技能集。UCP 是 Google、Shopify 等 20+ 合作伙伴共建的开放协议，让 AI agent 能发现商家并完成交易。

## 做什么

这些 skill 把 AI agent 变成 UCP 对接专家。给它一个商家网站 URL，它会：

1. **审计**网站的 UCP 就绪度（structured data、支付方式、API）
2. **生成** `/.well-known/ucp` 商家 profile
3. **映射**商品数据到 UCP catalog schema
4. **搭建** checkout API（基于官方 samples）
5. **验证**对接结果（调用官方工具）

```
商家 URL → 审计 → 生成 profile → 映射 catalog → 搭 checkout → 验证 → 上线 UCP
```

## 技能列表

| 技能 | 功能 | 脚本 |
|------|------|------|
| **ucp-audit** | 扫描网站，评分 0-100，识别可复用资产和缺失项 | `audit_site.py` |
| **ucp-profile** | 生成标准 `/.well-known/ucp` 商家 profile JSON | `generate_profile.py` |
| **ucp-catalog** | 映射 Shopify / WooCommerce / CSV 商品数据到 UCP 格式 | `map_catalog.py` |
| **ucp-checkout** | 基于[官方 samples](https://github.com/Universal-Commerce-Protocol/samples) 搭建 checkout API | SKILL.md |
| **ucp-validate** | 验证 profile 结构 + URL 可达性，推荐官方 `ucp-schema` CLI 做深度验证 | `validate_ucp.py` |

## 快速开始

```bash
pip install requests beautifulsoup4 jsonschema

# 1. 审计
python skills/ucp-audit/scripts/audit_site.py https://allbirds.com

# 2. 生成 profile
python skills/ucp-profile/scripts/generate_profile.py \
  --domain example.com --name "我的店铺" --payment stripe --transport rest

# 3. 映射商品
python skills/ucp-catalog/scripts/map_catalog.py \
  --source shopify --url https://allbirds.com --currency USD

# 4. 验证
python skills/ucp-validate/scripts/validate_ucp.py https://allbirds.com
```

## 真实网站测试结果

| 网站 | 审计得分 | 验证 | 备注 |
|------|---------|------|------|
| allbirds.com | 65/100 | PASS 11/11 | Shopify，MCP 传输 |
| glossier.com | 90/100 | PASS 11/11 | Shopify，MCP 传输 |
| puddingheroes.com | 5/100 | FAIL 16/42 | 非标准格式，被正确标记 |

## 验证方式

不重复造轮子，验证引用官方工具：

| 层级 | 工具 | 来源 |
|------|------|------|
| Profile 结构 | 我们的 `validate_ucp.py` | 检查必填字段、命名空间、URL 可达性 |
| 完整 Schema 验证 | [`ucp-schema`](https://github.com/Universal-Commerce-Protocol/ucp-schema) | 官方 Rust CLI |
| Checkout 行为 | [`conformance`](https://github.com/Universal-Commerce-Protocol/conformance) | 官方测试套件（12 个测试文件） |
| 外部发现 | [UCPchecker.com](https://ucpchecker.com) | 社区验证器（2800+ 商家） |

## 安全

UCP 内置了四层安全机制：

- **消息签名**（RFC 9421）— ECDSA 签名所有请求/响应
- **AP2 Mandate** — 密码学级别的购买授权证明（SD-JWT）
- **Signals** — 平台观测的环境数据用于反欺诈
- **Buyer Consent** — GDPR/CCPA 合规的同意传输

## 协议

[MIT](LICENSE)
