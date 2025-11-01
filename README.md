# AstrBot ShutUp 插件
![:name](https://count.getloli.com/@astrbot_plugin_shutup?name=astrbot_plugin_shutup&theme=minecraft&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)


## 功能介绍

- 可以让机器人在指定时间内停止回复消息
- 支持自定义闭嘴时长，如 60s、1m、1h、1d 等
- 支持自定义指令，可在配置面板修改
- 定时闭嘴
- 修改群昵称显示闭嘴状态

## 使用方法

### 基本指令

- `闭嘴 [时长]`：让机器人闭嘴，默认时长 600 秒
  - 示例：`闭嘴 5m`(让机器人闭嘴 5 分钟)
  - 支持单位 s(秒) m(分钟) h(小时) d(天)
- `说话`：解除机器人闭嘴状态

## 配置项

在插件配置文件中可自定义以下设置：

- `shutup_commands`：闭嘴指令列表，默认 `闭嘴,stop`
- `unshutup_commands`：解除闭嘴指令列表，默认 `说话,停止闭嘴`
- `default_duration`：默认闭嘴时长(秒)，默认 `600`
- `shutup_reply`：闭嘴时的回复消息，支持占位符 `{duration}`(禁言时长，秒)和 `{expiry_time}`(禁言结束时间)，默认 `好的，我闭嘴了~`
- `unshutup_reply`：解除闭嘴时的回复消息，支持占位符 `{duration}` 和 `{expiry_time}`，默认 `好的，我恢复说话了~`
- `require_prefix`：是否启用前缀模式，默认`启用`
- `scheduled_shutup_enabled`:是否启用定时闭嘴，默认`关闭`
- `scheduled_shutup_times`:定时闭嘴时间段
- `group_card_update_enabled`:是否启用群昵称剩余时长显示
- `group_card_template`:群昵称显示模板
## 注意事项
- 闭嘴状态仅对当前会话有效
- 在闭嘴期间，可以随时使用解除指令让机器人恢复回复
- 定时闭嘴期间，无法通过指令解除(后续更新可能会加上)

## 更新日志
### ToDo
- [ ] 注册函数供LLM调用
- [x] 使用群昵称显示闭嘴状态

### v1.4
- 添加群昵称剩余时长显示功能
  - 支持自定义群昵称模板
  - 闭嘴结束后自动恢复原始群昵称
- 限制 default_duration 范围(0-86400秒)
  - 配置超出范围时自动修正并保存

### v1.3
- 添加logo
- 提高闭嘴优先级(可自定义)，理论上可以屏蔽大部分插件消息

### v1.2
- 修复前缀模式禁言失效的问题
- 添加定时闭嘴功能

### v1.1
- 将silence_map进行持久化存储，重启bot也不会丢失数据
- 添加前缀模式，开启后须带有指令前缀或@才会触发
- 修改日志输出

### v1.0
- 首次发布