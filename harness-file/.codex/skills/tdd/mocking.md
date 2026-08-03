# 何时使用 Mock

只在**系统边界**使用 Mock：

- 外部 API（支付、邮件等）
- 数据库（有时需要，但优先使用测试数据库）
- 时间和随机性
- 文件系统（有时需要）

不要 Mock：

- 自己的类或模块
- 内部协作者
- 任何你能控制的对象

## 面向可 Mock 性设计

在系统边界设计易于 Mock 的接口：

**1. 使用依赖注入**

传入外部依赖，而不是在内部创建：

```typescript
// 易于 Mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// 难以 Mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. 优先使用 SDK 风格接口，而不是通用 fetcher**

为每个外部操作创建专用函数，不要用一个包含条件逻辑的通用函数：

```typescript
// 好：每个函数都可以独立 Mock
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// 坏：Mock 需要在 Mock 内部编写条件逻辑
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

SDK 风格意味着：
- 每个 Mock 返回一种明确的数据结构
- 测试设置中不需要条件逻辑
- 更容易看出测试覆盖了哪些端点
- 每个端点具备类型安全
