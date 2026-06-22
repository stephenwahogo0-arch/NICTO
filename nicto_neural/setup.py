from setuptools import setup

setup(
    name="nicto-neural",
    version="1.0.0",
    description="NICTO Neural Core V1 - HYPERBRAIN EVOLUTION ENGINE",
    author="NICTO AI",
    packages=[
        "nicto_neural",
        "nicto_neural.api",
        "nicto_neural.brain",
        "nicto_neural.evolution",
        "nicto_neural.execution",
        "nicto_neural.learning",
        "nicto_neural.memory",
        "nicto_neural.neural",
        "nicto_neural.perception",
        "nicto_neural.reasoning",
        "nicto_neural.safety",
        "nicto_neural.tests",
    ],
    package_dir={"nicto_neural": "."},
    install_requires=[
        "torch>=2.0.0",
        "numpy>=1.20.0",
    ],
    extras_require={
        "faiss": ["faiss-cpu>=1.7.0"],
    },
    python_requires=">=3.8",
)
