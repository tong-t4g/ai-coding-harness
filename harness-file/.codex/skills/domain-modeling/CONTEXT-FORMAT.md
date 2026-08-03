# CONTEXT.md 格式

## 结构

```md
# {Context Name}

{用一两句话描述该上下文是什么，以及它为什么存在。}

## 统一语言

**Order**:
{用一两句话描述该术语}
_避免使用_: Purchase、transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account
```

## 规则

- **保持明确立场。** 同一概念存在多个词时，选出最佳术语，并将其它词列在 `_避免使用_` 下。
- **定义要紧凑。** 最多一两句话。定义它“是什么”，而不是它“做什么”。
- **只收录该项目上下文特有的术语。** 通用编程概念（超时、错误类型、工具模式）即使被项目大量使用，也不属于此处。添加术语前先问：这是该上下文独有的概念，还是通用编程概念？只收录前者。
- **在自然形成术语簇时使用子标题分组。** 如果所有术语都属于一个连贯领域，使用扁平列表即可。

## 单上下文与多上下文仓库

**单上下文（大多数仓库）：** 仓库根目录有一个 `CONTEXT.md`。

**多上下文：** 仓库根目录的 `CONTEXT-MAP.md` 列出各上下文的位置及它们之间的关系：

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md) — 接收并跟踪客户订单
- [Billing](./src/billing/CONTEXT.md) — 生成发票并处理付款
- [Fulfillment](./src/fulfillment/CONTEXT.md) — 管理仓库拣货和发货

## Relationships

- **Ordering → Fulfillment**：Ordering 发送 `OrderPlaced` 事件；Fulfillment 消费该事件并开始拣货
- **Fulfillment → Billing**：Fulfillment 发送 `ShipmentDispatched` 事件；Billing 消费该事件并生成发票
- **Ordering ↔ Billing**：共享 `CustomerId` 和 `Money` 类型
```

skill 按以下规则推断适用的结构：

- 如果存在 `CONTEXT-MAP.md`，读取它以查找上下文
- 如果只有根目录 `CONTEXT.md`，则为单上下文
- 如果两者都不存在，在第一个术语确定时按需创建根目录 `CONTEXT.md`

存在多个上下文时，推断当前主题关联哪个上下文；无法确定时询问用户。
