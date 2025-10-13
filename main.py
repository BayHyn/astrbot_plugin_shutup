from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import logger
import time
import re
import os
import json
from datetime import datetime


@register("astrbot_plugin_shutup", "Railgun19457", "一个简单的插件，让bot闭嘴", "v1.2")
class ShutupPlugin(Star):
    def __init__(self, context: Context, config):
        super().__init__(context)
        self.config = config
        self.wake_prefix: list[str] = self.context.get_config().get("wake_prefix", [])
        # 直接获取配置项中的列表
        self.shutup_cmds = config.get("shutup_commands", ["闭嘴", "stop"])
        self.unshutup_cmds = config.get("unshutup_commands", ["说话", "停止闭嘴"])
        self.require_prefix = config.get("require_prefix", False)
        # 支持字符串配置，转换为列表
        if isinstance(self.shutup_cmds, str):
            self.shutup_cmds = re.split(r"[\s,]+", self.shutup_cmds)
        if isinstance(self.unshutup_cmds, str):
            self.unshutup_cmds = re.split(r"[\s,]+", self.unshutup_cmds)
        self.default_duration = config.get("default_duration", 600)
        self.shutup_reply = config.get("shutup_reply", "好的，我闭嘴了~")
        self.unshutup_reply = config.get("unshutup_reply", "好的，我恢复说话了~")

        # 定时闭嘴配置
        self.scheduled_enabled = config.get("scheduled_shutup_enabled", False)
        self.scheduled_times_text = config.get("scheduled_shutup_times", "23:00-07:00")
        self.scheduled_time_ranges = self._parse_time_ranges(self.scheduled_times_text)

        self.silence_map = {}
        self.data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "plugin_data",
            "astrbot_plugin_shutup",
        )
        self.silence_map_path = os.path.join(self.data_dir, "silence_map.json")
        self._load_silence_map()

        if self.scheduled_enabled:
            time_ranges_str = ", ".join(
                [f"{start}-{end}" for start, end in self.scheduled_time_ranges]
            )
            logger.info(
                f"[Shutup] 已加载 | 指令: {self.shutup_cmds} & {self.unshutup_cmds} | 默认时长: {self.default_duration}s | 定时: {time_ranges_str}"
            )
        else:
            logger.info(
                f"[Shutup] 已加载 | 指令: {self.shutup_cmds} & {self.unshutup_cmds} | 默认时长: {self.default_duration}s"
            )

    def _parse_time_ranges(self, time_text: str) -> list[tuple[str, str]]:
        """解析时间范围文本

        Args:
            time_text: 时间范围文本，每行一个，格式: HH:MM-HH:MM

        Returns:
            list[tuple[str, str]]: 时间范围列表，每个元素是 (开始时间, 结束时间)
        """
        time_ranges = []
        lines = time_text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):  # 跳过空行和注释
                continue

            # 匹配 HH:MM-HH:MM 格式
            match = re.match(r"^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$", line)
            if match:
                start_time = match.group(1)
                end_time = match.group(2)
                # 验证时间格式
                try:
                    datetime.strptime(start_time, "%H:%M")
                    datetime.strptime(end_time, "%H:%M")
                    time_ranges.append((start_time, end_time))
                except ValueError:
                    logger.warning(f"[Shutup] ⚠️ 无效的时间格式: {line}")
            else:
                logger.warning(f"[Shutup] ⚠️ 无法解析时间范围: {line}")

        if not time_ranges and self.scheduled_enabled:
            logger.warning("[Shutup] ⚠️ 未配置有效的定时时间段，定时闭嘴将不会生效")

        return time_ranges

    def _load_silence_map(self):
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            if os.path.exists(self.silence_map_path):
                with open(self.silence_map_path, "r", encoding="utf-8") as f:
                    self.silence_map = json.load(f)
                # json只能存str->float，确保float类型
                self.silence_map = {k: float(v) for k, v in self.silence_map.items()}
                if self.silence_map:
                    logger.info(f"[Shutup] 加载了 {len(self.silence_map)} 条禁言记录")
        except Exception as e:
            logger.warning(f"[Shutup] ⚠️ 加载禁言记录失败: {e}")

    def _save_silence_map(self):
        try:
            with open(self.silence_map_path, "w", encoding="utf-8") as f:
                json.dump(self.silence_map, f)
        except Exception as e:
            logger.warning(f"[Shutup] ⚠️ 保存禁言记录失败: {e}")

    def _is_in_scheduled_time(self) -> bool:
        """检查当前时间是否在定时闭嘴时间段内

        Returns:
            bool: True 表示在定时闭嘴时间段内
        """
        if not self.scheduled_enabled or not self.scheduled_time_ranges:
            return False

        try:
            now = datetime.now()
            current_time = now.hour * 60 + now.minute  # 转换为分钟数

            # 检查是否在任意一个时间段内
            for start_time_str, end_time_str in self.scheduled_time_ranges:
                # 解析开始和结束时间
                start_h, start_m = map(int, start_time_str.split(":"))
                end_h, end_m = map(int, end_time_str.split(":"))
                start_minutes = start_h * 60 + start_m
                end_minutes = end_h * 60 + end_m

                # 处理跨天的情况（例如 23:00 - 07:00）
                if start_minutes <= end_minutes:
                    # 不跨天的情况（例如 08:00 - 18:00）
                    if start_minutes <= current_time <= end_minutes:
                        return True
                else:
                    # 跨天的情况（例如 23:00 - 07:00）
                    if current_time >= start_minutes or current_time <= end_minutes:
                        return True

            return False
        except Exception as e:
            logger.warning(f"[Shutup] ⚠️ 检查定时配置失败: {e}")
            return False

    def _check_prefix(self, event: AstrMessageEvent) -> bool:
        """检查消息是否满足前缀要求

        Returns:
            bool: True 表示满足前缀要求（或不需要前缀），False 表示不满足前缀要求
        """
        if not self.require_prefix:
            return True

        chain = event.get_messages()
        if not chain:
            return False

        first_seg = chain[0]
        # 前缀触发
        if isinstance(first_seg, Comp.Plain):
            return any(first_seg.text.startswith(prefix) for prefix in self.wake_prefix)
        # @bot触发
        elif isinstance(first_seg, Comp.At):
            return str(first_seg.qq) == str(event.get_self_id())
        else:
            return False

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_message(self, event: AstrMessageEvent):
        text = event.get_message_str().strip()
        origin = event.unified_msg_origin

        # 1. 首先检查是否是控制指令（闭嘴/说话）
        is_control_cmd = False
        for cmd in self.shutup_cmds + self.unshutup_cmds:
            if text.startswith(cmd):
                is_control_cmd = True
                break

        # 2. 如果是控制指令，需要检查前缀要求
        if is_control_cmd:
            if not self._check_prefix(event):
                return

            # 3. 处理闭嘴指令
            for cmd in self.shutup_cmds:
                if text.startswith(cmd):
                    m = re.match(rf"^{re.escape(cmd)}\s*(\d+)([smhd])?", text)
                    if m:
                        val = int(m.group(1))
                        unit = m.group(2) or "s"
                        dur = val * {"s": 1, "m": 60, "h": 3600, "d": 86400}.get(
                            unit, 1
                        )
                    else:
                        dur = self.default_duration

                    self.silence_map[origin] = time.time() + dur
                    self._save_silence_map()
                    expiry_time = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(self.silence_map[origin])
                    )
                    logger.info(
                        f"[Shutup] 🔇 已禁言 | 时长: {dur}s | 到期: {expiry_time}"
                    )
                    reply = self.shutup_reply.format(
                        duration=dur, expiry_time=expiry_time
                    )
                    yield event.plain_result(reply)
                    event.stop_event()
                    return

            # 4. 处理解除闭嘴指令
            for cmd in self.unshutup_cmds:
                if text.startswith(cmd):
                    # 先获取旧的过期时间用于计算已禁言时长
                    old_expiry = self.silence_map.get(origin)
                    if old_expiry:
                        # 计算实际禁言了多长时间
                        duration = int(
                            time.time() - (old_expiry - self.default_duration)
                        )
                    else:
                        duration = 0

                    self.silence_map.pop(origin, None)
                    self._save_silence_map()
                    expiry_time = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(time.time())
                    )
                    logger.info(f"[Shutup] 🔊 已解除禁言 | 已禁言: {duration}s")
                    reply = self.unshutup_reply.format(
                        duration=duration, expiry_time=expiry_time
                    )
                    yield event.plain_result(reply)
                    event.stop_event()
                    return

        # 5. 检查定时闭嘴（在检查禁言状态之前，但控制指令可以绕过）
        if self._is_in_scheduled_time():
            logger.info("[Shutup] ⏰ 定时闭嘴生效中")
            event.should_call_llm(False)
            event.stop_event()
            return

        # 6. 如果不是控制指令，检查是否在禁言状态
        expiry = self.silence_map.get(origin)
        if expiry:
            current_time = time.time()
            if current_time < expiry:
                # 仍在禁言期内，拦截非控制指令的消息
                remaining = int(expiry - current_time)
                logger.info(
                    f"[Shutup] 🚫 消息已拦截 | 来源: {origin} | 剩余: {remaining}s"
                )
                event.should_call_llm(False)
                event.stop_event()
                return
            else:
                # 禁言已过期，自动清理
                logger.info("[Shutup] ⏰ 禁言已自动过期")
                self.silence_map.pop(origin, None)
                self._save_silence_map()

    async def terminate(self):
        logger.info("[Shutup] 已卸载插件")
