"""Smoke test: verify all KYROSAI modules import correctly."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "kyros-core", "src"))

print("Testing KYROSAI module imports...")

from kyros import (
    KyrosConfig, ModelConfig, MemoryConfig, DaemonConfig,
    ModelProvider, create_provider,
    MemorySystem,
    Tool, ToolRegistry,
    FileReadTool, FileWriteTool, FileEditTool, GlobTool, GrepTool,
    BashTool,
    WebFetchTool, WebSearchTool,
    CryptoCreateWalletTool, CryptoBalanceTool, CryptoSendTool, CryptoAddressTool,
    NmapScanTool, GobusterTool, SqlmapTool, KyrosWebScanTool,
    HashcatTool, HydraTool, MetasploitTool, SearchsploitTool,
    AmassTool, DirbTool, WpscanTool, WiresharkTool, Enum4linuxTool, JohnRipperTool,
    KyrosReadOwnTool, KyrosWriteOwnTool, KyrosSelfReviewTool,
    ImageGenerateTool, PatternGenerateTool,
    GifGenerateTool, VideoGenerateTool,
    SpeakTool, SpeakDirectTool, ListVoicesTool,
    Orchestrator, OrchestratorConfig, TicketStatus,
    AgentVariant, create_variant, HEAVYWEIGHT_CONFIG, SONNET_CONFIG, MYTHOS_CONFIG,
    KyrosHeavyweight, KyrosSonnet, KyrosMythos,
    ScreenController, InputController,
    AutomationStep, StepType,
    MCPRegistry, mcp_registry,
    MCPServer, MCPServerConfig, MCPClient,
    CodeSecurityProtocol, MCPSecureSandbox, ASL3Boundary, SIEMAnalyst,
    AutopilotEngine, AutopilotConfig, AutopilotStatus,
    DEFAULT_AUTOPILOT_TASKS, CryptoMarketMonitor, WalletBalanceCheck,
    FinanceManager,
    ConnectionManager, Connection, ConnectionType,
    DeviceController, DeviceType, DeviceConnection, DeviceCommand, CommandResult,
    GameEngine, GameGenre, GameProject, ProjectGenerator,
    EvolutionEngine, EvolutionConfig,
    DreamEngine, DreamConfig,
    MeshEngine, MeshConfig, MeshNode, NodeStatus,
    EarnWallet,
    LaptopMiner, MinerConfig,
    SkillRuntime,
    register_production_skills,
    KyrosDaemon,
    app,
)
print("OK - all top-level imports resolved")

# Verify constructor / instance creation
assert KyrosConfig is not None
assert ModelConfig() is not None
assert MemoryConfig() is not None
assert DaemonConfig() is not None
print("OK - config classes instantiate")

# Verify providers
assert create_provider(ModelConfig(provider="local")) is not None
print("OK - provider factory works")

# Verify tools
registry = ToolRegistry()
registry.register(FileReadTool())
registry.register(BashTool())
assert len(registry.list_tools()) == 2
print("OK - ToolRegistry works")

# Verify orchestrator
orch = Orchestrator(OrchestratorConfig())
agent = orch.add_agent("test", "worker")
ticket = orch.create_ticket("Test", "Testing")
assert orch.report_ticket(ticket["id"], TicketStatus.RESOLVED, "done")["success"]
print("OK - Orchestrator works")

# Verify variants
assert create_variant("kyros-heavyweight")
assert create_variant("kyros-sonnet")
assert create_variant("kyros-mythos")
print("OK - Variant factory works")

# Verify cua
ctrl = ScreenController()
assert ctrl.list_screens() is not None
input_ctrl = InputController()
assert input_ctrl.click(100, 100)
print("OK - CUA controllers work")

# Verify MCP
assert mcp_registry.register("test", {"type": "local"})["success"]
assert MCPClient("test").server_info is not None
print("OK - MCP works")

# Verify security
protocol = CodeSecurityProtocol()
assert ASL3Boundary().classify_and_filter("ls -la").classification == "safe"
assert SIEMAnalyst().analyst_id is not None
print("OK - Security modules work")

# Verify autopilot
engine = AutopilotEngine(AutopilotConfig())
assert engine.start()["success"]
assert engine.status_report()["running"]
print("OK - Autopilot works")

# Verify devices
dev_ctrl = DeviceController()
dev_ctrl.register_device("test", DeviceType.SERVER, DeviceConnection("ssh", "localhost", 22))
assert len(dev_ctrl.list_devices()) == 1
print("OK - Device controller works")

# Verify game engine
import asyncio
async def check_game():
    ge = GameEngine()
    result = await ge.generate_game("TestGame", "action")
    assert result["success"]
    games = await ge.list_games()
    assert len(games) == 1
    print("OK - Game engine works")
asyncio.run(check_game())

# Verify evolution
evo = EvolutionEngine(EvolutionConfig())
import asyncio
async def check_evo():
    assert await evo.start()
    assert evo.running
    print("OK - Evolution engine works")
asyncio.run(check_evo())

# Verify dream
dream = DreamEngine(DreamConfig())
import asyncio
async def check_dream():
    result = await dream.force_dream()
    assert result["success"]
    assert len(result["insights"]) > 0
    print("OK - Dream engine works")
asyncio.run(check_dream())

# Verify mesh
mesh = MeshEngine(MeshConfig())
mesh.add_node("node1", "192.168.1.1")
assert len(mesh.list_nodes()) == 1
task_id = mesh.submit_task("scan", {"target": "localhost"})
assert task_id is not None
print("OK - Mesh engine works")

# Verify earn
wallet = EarnWallet("test")
miner = LaptopMiner(MinerConfig())
assert miner.start()["success"]
assert miner.stats()["status"] == "running"
miner.stop()
print("OK - Earn modules work")

# Verify skills
runtime = SkillRuntime()
register_production_skills(runtime)
assert len(runtime.list_skills()) >= 15
print("OK - Production skills registered")

# Verify daemon
daemon = KyrosDaemon(DaemonConfig())
assert daemon.daemon_id is not None
print("OK - Daemon works")

# Verify API
assert app.title == "Kyros API"
print("OK - FastAPI app works")

print("\n=== ALL 45+ TESTS PASSED ===")
