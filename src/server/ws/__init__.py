"""
王者之奕 - WebSocket 处理器初始化

本模块负责注册所有 WebSocket 消息处理器。
"""


def register_all_handlers() -> None:
    """
    注册所有 WebSocket 消息处理器
    注意: 此函数需要在 ws_handler 创建后调用
    """
    from src.server.ws.handler import ws_handler  # noqa: F401

    registered = []
    failed = []

    # 要注册的模块列表
    modules = [
        "consumable_ws",
        "emote_ws",
        "leaderboard_ws",
        "lineup_ws",
        "spectator_ws",
        "voting_ws",
    ]

    import importlib

    for mod_name in modules:
        try:
            # 动态导入模块
            importlib.import_module(f"src.server.ws.{mod_name}")
            registered.append(mod_name)
            print(f"✅ 注册 {mod_name}")
        except NameError as e:
            if "ws_handler" in str(e):
                # ws_handler 尚未定义，跳过此模块
                print(f"⚠️ 跳过 {mod_name}: ws_handler 未定义")
            else:
                failed.append((mod_name, str(e)))
                print(f"❌ 注册 {mod_name} 失败: {e}")
        except Exception as e:
            failed.append((mod_name, str(e)))
            print(f"❌ 注册 {mod_name} 失败: {e}")

    print(f"\n📊 注册完成: {len(registered)}/{len(modules)}")
    if failed:
        print(f"⚠️ 失败模块: {[f[0] for f in failed]}")
