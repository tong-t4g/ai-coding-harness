# 业务隐性规则

## 广告投放状态字段 status 的隐性约定
- 背景：历史上前后端口头约定，`status = null` 表示“未初始化”，`status = 0` 表示“已关
  闭”
- 代码现状：后端代码中没有统一显式注释，前端页面逻辑依赖这个区别
- 风险：如果把 `null` 和 `0` 合并处理，可能导致页面状态判断错误
- 处理要求：
- 修改该字段相关逻辑前，先确认前端依赖
- 不要擅自把 null 归一化成默认值
- 如确需调整，必须在 OpenSpec design 中明确说明影响面

## 单元详情返回的时候需要有contentResponse
- 背景：历史上前后端口头约定，后端会将前端传入的contentId转化成contentResponse，返回后
  用于前端展示
- 代码现状：后端代码中没有统一显式注释，前端页面逻辑依赖contentResponse进行展示
- 风险：如果缺失contentResponse前端展示会报错
- 处理要求：
- 修改该接口相关逻辑时，需要保留当前contentResponse逻辑
- 如确需调整，必须在 OpenSpec design 中明确说明影响面