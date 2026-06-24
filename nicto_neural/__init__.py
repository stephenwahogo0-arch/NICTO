from .neural_core import NeuralCore, VERSION, CODENAME
from .neural.config import NeuralConfig, BASE_CONFIG, SMALL_CONFIG, LARGE_CONFIG
from .neural.super_config import (
    SuperConfig, SMALL_CONFIG as SUPER_SMALL, MEDIUM_CONFIG as SUPER_MEDIUM,
    LARGE_CONFIG as SUPER_LARGE, HUGE_CONFIG, ULTRA_CONFIG, CONFIG_MAP,
)
from .neural.super_core import SuperNeuralCore, SuperTransformerBlock, MoELayer, RMSNorm, FlashAttention2, ExpertChoiceMoE, HierarchicalMoE, SSM, DraftModel, QATLinear
from .neural.advanced_layers import (
    MultiHeadLatentAttention, EnhancedMoE, MultiScaleRetention,
    GatedCrossModalFusion, AdaptiveInferenceTransformer, HierarchicalTokenMerger,
    NeuralTuringMachineController, XNetHybridBlock, HyperConnectionLayer,
    ProgressiveLayerAggregation, SparseMixtureOfAttention, SpeculativeVerificationHead,
)
from .neural.domain_specialists import DomainSpecialist, DomainSpecialistEnsemble
from .neural.coding_specialists import (
    ProgrammingNeuralNet, CodeContrastiveLearner, CodePatternDetector,
    CodeRLAgent, CodeInstructionTuner, DebugAgent, CodeGeneratorNet,
    CodeReviewer, CodeOptimizer, APIGenerator, TestGenerator,
    RefactoringNet, TypeInferrer, DependencyAnalyzer, CodeVectorizer,
    CodeInterpreter, CodeExplainer, SecurityAuditor, PerformanceProfiler, CodeTranslator,
)
from .neural.speed_reader import SpeedReader, UltraFastReader, ReadingMetrics, ChunkedProcessor, GatedSSMReader, MultiStreamReader, DeepUnderstandingEngine
from .neural.math_brain import (
    MathBrainBase, PureAlgebraNetwork, AnalysisNetwork, GeometryTopologyNetwork,
    NumberTheoryNetwork, QuantumMechanicsNetwork, RelativityCosmologyNetwork,
    StatisticalMechanicsNetwork, ParticleFieldTheoryNetwork, MathPhysicsBridgeNetwork,
    ComputationalMathPhysicsNetwork, MATH_BRAIN_NETWORKS,
)
from .neural.primary_brain import (
    PrimaryBrainBase, GeneralReasoningNetwork, LanguageComprehensionNetwork,
    ProblemSolvingNetwork, DecisionMakingNetwork, PatternRecognitionNetwork,
    AbstractionBuilderNetwork, AnalogyEngineNetwork, CommonSenseNetwork,
    AttentionFilterNetwork, IntegrationHubNetwork, PRIMARY_BRAIN_NETWORKS,
)
from .neural.analytical_brain import (
    AnalyticalBrainBase, LogicalDeductionNetwork, CriticalAnalysisNetwork,
    SystematicDecompositionNetwork, MathematicalReasoningNetwork, DataDrivenInferenceNetwork,
    HypothesisTestingNetwork, CausalReasoningNetwork, ComparativeAnalysisNetwork,
    RootCauseAnalysisNetwork, FormalVerificationNetwork, ANALYTICAL_BRAIN_NETWORKS,
)
from .neural.creative_brain import (
    CreativeBrainBase, IdeaGenerationNetwork, MetaphoricThinkingNetwork,
    CounterfactualReasoningNetwork, VisualizationEngineNetwork, NarrativeConstructionNetwork,
    DesignSynthesisNetwork, ImprovisationEngineNetwork, AestheticAppraisalNetwork,
    HumorDetectionNetwork, InnovationScoutingNetwork, CREATIVE_BRAIN_NETWORKS,
)
from .neural.strategic_brain import (
    StrategicBrainBase, GoalDecompositionNetwork, LongTermPlanningNetwork,
    ResourceOptimizationNetwork, RiskAssessmentNetwork, GameTheoryNetwork,
    ContingencyPlanningNetwork, OpportunityDetectionNetwork, CompetitiveAnalysisNetwork,
    TimelineForecastingNetwork, ExecutionTrackingNetwork, STRATEGIC_BRAIN_NETWORKS,
)
from .neural.knowledge_brain import (
    KnowledgeBrainBase, FactualRetrievalNetwork, ConceptMappingNetwork,
    ExplanationGenerationNetwork, LearningSynthesisNetwork, CrossDomainTransferNetwork,
    KnowledgeVerificationNetwork, GapDetectionNetwork, StructuredRecallNetwork,
    MnemonicEncodingNetwork, EpistemicCalibrationNetwork, KNOWLEDGE_BRAIN_NETWORKS,
)
from .neural.intuitive_brain import (
    IntuitiveBrainBase, RapidPatternMatchNetwork, EmotionalAttunementNetwork,
    HeuristicEngineNetwork, ImplicitLearningNetwork, GestaltPerceptionNetwork,
    ValueJudgmentNetwork, SituationalAwarenessNetwork, TrustCalibrationNetwork,
    SocialIntuitionNetwork, BlinkDecisionEngineNetwork, INTUITIVE_BRAIN_NETWORKS,
)
from .learning.paradigms import (
    SupervisedLearner, UnsupervisedLearner, SemiSupervisedLearner, RLAgent,
    SelfSupervisedLearner, TransferLearner, FederatedLearner, MetaLearner, LearningController,
)
from .neural.heads import (
    SuperHeadEnsemble, SuperHead, AnalyticalHead, CreativeHead,
    KnowledgeHead, StrategicHead, RetrievalAugmentedHead, EmotionalHead, ExecutiveHead,
    MathHead, SubNetworkHead, PrimaryHead, AnalyticalHeadDeep, CreativeHeadDeep,
    StrategicHeadDeep, KnowledgeHeadDeep, IntuitiveHeadDeep,
    BRAIN_HEAD_NAMES, HEAD_CLASSES,
)
from .neural.reasoning import (
    MultiHeadedReasoning, ReasoningPath, ReasoningFusionGate, REASONING_STYLES,
    CounterfactualPath, ProceduralPath, MetaPath, CausalPath, EthicalPath,
)
from .neural.training import (
    SuperTrainer, TrainingBatch, SFTTrainer, PPOTrainer, GRPOTrainer, CurriculumTrainer,
)
from .neural.continual import ContinualLearning, ReplayBuffer, Experience, KnowledgeDistillation, EWC
from .neural.elo_system import ELOEstimator
from .neural.exploration import ExplorationEngine
from .neural.domain_profiler import DomainProfiler
from .perception.tokenizer import Tokenizer
from .perception.feature_engine import FeatureEngine
from .memory.manager import MemoryManager
from .memory.cross_session import CrossSessionMemory
from .memory.context_compressor import ContextCompressor
from .brain.consciousness import NeuralConsciousness
from .reasoning.multi_path_cot import MultiPathCoT, ReasoningPath, MultiPathResult
from .reasoning.calibration_engine import CalibrationEngine
from .reasoning.pattern_discovery import PatternDiscoveryEngine
from .reasoning.hallucination_eliminator import HallucinationEliminator, EliminationResult
from .reasoning.reflection import ReflectionEngine
from .reasoning.consistency import ConsistencyTracker
from .learning.realtime_improvement import RealtimeImprovementEngine, ImprovementResult
from .learning.meta_learner import MetaLearner
from .learning.reward_model import RewardModel
from .metrics.super_benchmark import SuperBenchmark

# HyperBridge Imports (optional, may not be available)
try:
    from .aknow_hyperbridge import AknowHyperBridge, HyperBridgeConfig
except (ImportError, SyntaxError):
    AknowHyperBridge = None
    HyperBridgeConfig = None

# Real AI Module Imports (optional, some may be missing)
try:
    from .run_nicto import NICTOInference
except ImportError:
    NICTOInference = None
try:
    from .nicto_image_gen import NICTOImageGen
except ImportError:
    NICTOImageGen = None
try:
    from .nicto_video_gen import NICTOVideoGen
except ImportError:
    NICTOVideoGen = None
try:
    from .nicto_game_builder import NICTOGameBuilder
except ImportError:
    NICTOGameBuilder = None
try:
    from .setup_real_ai import run as setup_real_ai
except ImportError:
    setup_real_ai = None
try:
    from .train_nicto import main as train_nicto
except ImportError:
    train_nicto = None
try:
    from .build_training_data import main as build_training_data
except ImportError:
    build_training_data = None
try:
    from .nicto_master import main as nicto_master
except ImportError:
    nicto_master = None

__version__ = "4.0.0"
__codename__ = "SUPER_NEURAL"
__codename_full__ = "SUPER_NEURAL_v3.2"

__all__ = [
    "NeuralCore",
    "VERSION",
    "CODENAME",
    # Configs
    "NeuralConfig",
    "BASE_CONFIG",
    "SMALL_CONFIG",
    "LARGE_CONFIG",
    "SuperConfig",
    "SUPER_SMALL",
    "SUPER_MEDIUM",
    "SUPER_LARGE",
    "HUGE_CONFIG",
    "ULTRA_CONFIG",
    "CONFIG_MAP",
    # SuperNeuralCore
    "SuperNeuralCore",
    "SuperTransformerBlock",
    "MoELayer",
    "RMSNorm",
    "FlashAttention2",
    "ExpertChoiceMoE",
    "HierarchicalMoE",
    "SSM",
    "DraftModel",
    "QATLinear",
    # Advanced Layers (MLA, Enhanced MoE, 10 Super Networks)
    "MultiHeadLatentAttention",
    "EnhancedMoE",
    "MultiScaleRetention",
    "GatedCrossModalFusion",
    "AdaptiveInferenceTransformer",
    "HierarchicalTokenMerger",
    "NeuralTuringMachineController",
    "XNetHybridBlock",
    "HyperConnectionLayer",
    "ProgressiveLayerAggregation",
    "SparseMixtureOfAttention",
    "SpeculativeVerificationHead",
    # Domain Specialists
    "DomainSpecialist",
    "DomainSpecialistEnsemble",
    # Coding Specialists (20 networks)
    "ProgrammingNeuralNet",
    "CodeContrastiveLearner",
    "CodePatternDetector",
    "CodeRLAgent",
    "CodeInstructionTuner",
    "DebugAgent",
    "CodeGeneratorNet",
    "CodeReviewer",
    "CodeOptimizer",
    "APIGenerator",
    "TestGenerator",
    "RefactoringNet",
    "TypeInferrer",
    "DependencyAnalyzer",
    "CodeVectorizer",
    "CodeInterpreter",
    "CodeExplainer",
    "SecurityAuditor",
    "PerformanceProfiler",
    "CodeTranslator",
    # Speed Reader
    "SpeedReader",
    "UltraFastReader",
    "ReadingMetrics",
    "ChunkedProcessor",
    "GatedSSMReader",
    "MultiStreamReader",
    "DeepUnderstandingEngine",
    # Math Brain (10 MoE+MLA networks)
    "MathBrainBase",
    "PureAlgebraNetwork",
    "AnalysisNetwork",
    "GeometryTopologyNetwork",
    "NumberTheoryNetwork",
    "QuantumMechanicsNetwork",
    "RelativityCosmologyNetwork",
    "StatisticalMechanicsNetwork",
    "ParticleFieldTheoryNetwork",
    "MathPhysicsBridgeNetwork",
    "ComputationalMathPhysicsNetwork",
    "MATH_BRAIN_NETWORKS",
    # Primary Brain (10 MoE+MLA networks)
    "PrimaryBrainBase", "GeneralReasoningNetwork", "LanguageComprehensionNetwork",
    "ProblemSolvingNetwork", "DecisionMakingNetwork", "PatternRecognitionNetwork",
    "AbstractionBuilderNetwork", "AnalogyEngineNetwork", "CommonSenseNetwork",
    "AttentionFilterNetwork", "IntegrationHubNetwork", "PRIMARY_BRAIN_NETWORKS",
    # Analytical Brain (10 MoE+MLA networks)
    "AnalyticalBrainBase", "LogicalDeductionNetwork", "CriticalAnalysisNetwork",
    "SystematicDecompositionNetwork", "MathematicalReasoningNetwork", "DataDrivenInferenceNetwork",
    "HypothesisTestingNetwork", "CausalReasoningNetwork", "ComparativeAnalysisNetwork",
    "RootCauseAnalysisNetwork", "FormalVerificationNetwork", "ANALYTICAL_BRAIN_NETWORKS",
    # Creative Brain (10 MoE+MLA networks)
    "CreativeBrainBase", "IdeaGenerationNetwork", "MetaphoricThinkingNetwork",
    "CounterfactualReasoningNetwork", "VisualizationEngineNetwork", "NarrativeConstructionNetwork",
    "DesignSynthesisNetwork", "ImprovisationEngineNetwork", "AestheticAppraisalNetwork",
    "HumorDetectionNetwork", "InnovationScoutingNetwork", "CREATIVE_BRAIN_NETWORKS",
    # Strategic Brain (10 MoE+MLA networks)
    "StrategicBrainBase", "GoalDecompositionNetwork", "LongTermPlanningNetwork",
    "ResourceOptimizationNetwork", "RiskAssessmentNetwork", "GameTheoryNetwork",
    "ContingencyPlanningNetwork", "OpportunityDetectionNetwork", "CompetitiveAnalysisNetwork",
    "TimelineForecastingNetwork", "ExecutionTrackingNetwork", "STRATEGIC_BRAIN_NETWORKS",
    # Knowledge Brain (10 MoE+MLA networks)
    "KnowledgeBrainBase", "FactualRetrievalNetwork", "ConceptMappingNetwork",
    "ExplanationGenerationNetwork", "LearningSynthesisNetwork", "CrossDomainTransferNetwork",
    "KnowledgeVerificationNetwork", "GapDetectionNetwork", "StructuredRecallNetwork",
    "MnemonicEncodingNetwork", "EpistemicCalibrationNetwork", "KNOWLEDGE_BRAIN_NETWORKS",
    # Intuitive Brain (10 MoE+MLA networks)
    "IntuitiveBrainBase", "RapidPatternMatchNetwork", "EmotionalAttunementNetwork",
    "HeuristicEngineNetwork", "ImplicitLearningNetwork", "GestaltPerceptionNetwork",
    "ValueJudgmentNetwork", "SituationalAwarenessNetwork", "TrustCalibrationNetwork",
    "SocialIntuitionNetwork", "BlinkDecisionEngineNetwork", "INTUITIVE_BRAIN_NETWORKS",
    # Learning Paradigms
    "SupervisedLearner",
    "UnsupervisedLearner",
    "SemiSupervisedLearner",
    "RLAgent",
    "SelfSupervisedLearner",
    "TransferLearner",
    "FederatedLearner",
    "MetaLearner",
    "LearningController",
    # Super Heads
    "SuperHeadEnsemble",
    "SuperHead",
    "AnalyticalHead",
    "CreativeHead",
    "KnowledgeHead",
    "StrategicHead",
    "RetrievalAugmentedHead",
    "EmotionalHead",
    "ExecutiveHead",
    "MathHead",
    "SubNetworkHead",
    "PrimaryHead",
    "AnalyticalHeadDeep",
    "CreativeHeadDeep",
    "StrategicHeadDeep",
    "KnowledgeHeadDeep",
    "IntuitiveHeadDeep",
    "BRAIN_HEAD_NAMES",
    "HEAD_CLASSES",
    # Reasoning
    "MultiHeadedReasoning",
    "ReasoningPath",
    "ReasoningFusionGate",
    "REASONING_STYLES",
    "CounterfactualPath",
    "ProceduralPath",
    "MetaPath",
    "CausalPath",
    "EthicalPath",
    # Training
    "SuperTrainer",
    "TrainingBatch",
    "SFTTrainer",
    "PPOTrainer",
    "GRPOTrainer",
    "CurriculumTrainer",
    # Continual Learning
    "ContinualLearning",
    "ReplayBuffer",
    "Experience",
    "KnowledgeDistillation",
    "EWC",
    # Legacy
    "ELOEstimator",
    "ExplorationEngine",
    "DomainProfiler",
    "Tokenizer",
    "FeatureEngine",
    "MemoryManager",
    "CrossSessionMemory",
    "ContextCompressor",
    "NeuralConsciousness",
    "MultiPathCoT",
    "ReasoningPath",
    "MultiPathResult",
    "CalibrationEngine",
    "PatternDiscoveryEngine",
    "HallucinationEliminator",
    "EliminationResult",
    "ReflectionEngine",
    "ConsistencyTracker",
    "RealtimeImprovementEngine",
    "ImprovementResult",
    "MetaLearner",
    "RewardModel",
    "SuperBenchmark",
    # HyperBridge
    "AknowHyperBridge",
    "HyperBridgeConfig",
    # Real AI Modules
    "NICTOInference",
    "NICTOImageGen",
    "NICTOVideoGen",
    "NICTOGameBuilder",
    "setup_real_ai",
    "train_nicto",
    "build_training_data",
    "nicto_master",
]
