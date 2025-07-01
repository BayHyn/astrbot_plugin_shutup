from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import time
import re
import os
import json

@register("astrbot_plugin_shutup", "Railgun19457", "一个简单的插件，让bot闭嘴", "v1.0")
class ShutupPlugin(Star):
    def __init__(self, context: Context, config):
        super().__init__(context)
        self.config = config
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
        self.silence_map = {}
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "plugin_data", "astrbot_plugin_shutup")
        self.silence_map_path = os.path.join(self.data_dir, "silence_map.json")
        self._load_silence_map()
        logger.info(f"[ShutupPlugin] 已加载闭嘴指令: {self.shutup_cmds}")
        logger.info(f"[ShutupPlugin] 已加载解除闭嘴指令: {self.unshutup_cmds}")
        logger.info(f"[ShutupPlugin] 默认持续时间={self.default_duration}s, 闭嘴回复='{self.shutup_reply}', 恢复说话回复='{self.unshutup_reply}'")

    def _load_silence_map(self):
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            if os.path.exists(self.silence_map_path):
                with open(self.silence_map_path, "r", encoding="utf-8") as f:
                    self.silence_map = json.load(f)
                # json只能存str->float，确保float类型
                self.silence_map = {k: float(v) for k, v in self.silence_map.items()}
                logger.info(f"[ShutupPlugin] 已从 {self.silence_map_path} 加载silence_map")
        except Exception as e:
            logger.warning(f"[ShutupPlugin] 加载silence_map失败: {e}")

    def _save_silence_map(self):
        try:
            with open(self.silence_map_path, "w", encoding="utf-8") as f:
                json.dump(self.silence_map, f)
            logger.debug(f"[ShutupPlugin] 已保存silence_map到 {self.silence_map_path}")
        except Exception as e:
            logger.warning(f"[ShutupPlugin] 保存silence_map失败: {e}")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_message(self, event: AstrMessageEvent):
        text = event.get_message_str().strip()
        origin = event.unified_msg_origin
        logger.info(f"[ShutupPlugin] 收到来自 {origin} 的消息 '{text}'")
        logger.debug(f"[ShutupPlugin] 处理前当前silence_map: {self.silence_map}")
        # shutup
        for cmd in self.shutup_cmds:
            if text.startswith(cmd):
                logger.info(f"[ShutupPlugin] 正在激活 {origin} 的禁言")
                m = re.match(rf"^{re.escape(cmd)}\s*(\d+)([smhd])?", text)
                if m:
                    val = int(m.group(1))
                    unit = m.group(2) or "s"
                    dur = val * {"s":1, "m":60, "h":3600, "d":86400}.get(unit, 1)
                else:
                    dur = self.default_duration
                logger.info(f"[ShutupPlugin] 禁言持续时间={dur}s")
                self.silence_map[origin] = time.time() + dur
                self._save_silence_map()
                expiry_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.silence_map[origin]))
                reply = self.shutup_reply.format(duration=dur, expiry_time=expiry_time)
                yield event.plain_result(reply)
                event.stop_event()
                return
        # unshutup
        for cmd in self.unshutup_cmds:
            if text.startswith(cmd):
                logger.info(f"[ShutupPlugin] 正在移除 {origin} 的禁言")
                self.silence_map.pop(origin, None)
                self._save_silence_map()
                duration = int(time.time() - (self.silence_map.get(origin, time.time())))
                expiry_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                logger.debug(f"[ShutupPlugin] 取消禁言状态: 持续时间={duration}s, 到期时间={expiry_time}")
                reply = self.unshutup_reply.format(duration=duration, expiry_time=expiry_time)
                yield event.plain_result(reply)
                event.stop_event()
                return
        # silence active
        expiry = self.silence_map.get(origin)
        if expiry and time.time() < expiry:
            logger.debug(f"[ShutupPlugin] 来自 {origin} 的消息被抑制直到 {expiry}")
            event.should_call_llm(False)
            event.stop_event()
            return
        logger.debug(f"[ShutupPlugin] 消息 '{text}' 无禁言控制，正常通过")

    async def terminate(self):
        logger.info("[ShutupPlugin] 已卸载 shut up 插件")
        self.silence_map.clear()
        self._save_silence_map()
