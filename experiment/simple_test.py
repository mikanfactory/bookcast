#!/usr/bin/env python3
"""
Simple test script to verify agent system imports and basic functionality
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    print("🧪 Starting simple import test...")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path[0]}")
    
    # Test basic imports
    print("1. Testing agent_models import...")
    from experiment.agent_models import AgentConfig, Topic, AgentProcessResult
    print("   ✅ agent_models imported successfully")
    
    print("2. Testing topic_extractor_agent import...")
    from experiment.topic_extractor_agent import TopicExtractorAgent
    print("   ✅ topic_extractor_agent imported successfully")
    
    print("3. Testing script_generator_agent import...")
    from experiment.script_generator_agent import ScriptGeneratorAgent
    print("   ✅ script_generator_agent imported successfully")
    
    print("4. Testing script_integrator_agent import...")
    from experiment.script_integrator_agent import ScriptIntegratorAgent
    print("   ✅ script_integrator_agent imported successfully")
    
    print("5. Testing quality_evaluator_agent import...")
    from experiment.quality_evaluator_agent import QualityEvaluatorAgent
    print("   ✅ quality_evaluator_agent imported successfully")
    
    print("6. Testing script_agent_orchestrator import...")
    from experiment.script_agent_orchestrator import ScriptAgentOrchestrator
    print("   ✅ script_agent_orchestrator imported successfully")
    
    print("7. Testing basic object creation...")
    config = AgentConfig()
    print(f"   ✅ AgentConfig created: {config.target_duration_minutes}分, {config.target_topic_count}トピック")
    
    # Test external dependencies
    print("8. Testing external dependencies...")
    from google import genai
    print("   ✅ google-genai imported successfully")
    
    from bookcast.config import GEMINI_API_KEY
    print("   ✅ bookcast.config imported successfully")
    
    print("\n🎉 All imports successful! Ready for full testing.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nPlease check:")
    print("1. All required packages are installed")
    print("2. PYTHONPATH includes the project root")
    print("3. All files are in correct locations")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    
print("\n" + "="*50)