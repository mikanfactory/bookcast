#!/bin/bash
echo "🧪 Agent System Test Runner"
echo "=========================="

# Change to project root directory
cd "$(dirname "$0")/.."

echo "Current directory: $(pwd)"
echo "Project structure check:"
ls -la | grep -E "(bookcast|experiment)"
echo ""

echo "Step 1: Simple import test"
echo "--------------------------"
python experiment/simple_test.py
echo ""

if [ $? -eq 0 ]; then
    echo "Step 2: Full agent test"
    echo "----------------------"
    python experiment/main.py test
    echo ""
    
    if [ $? -eq 0 ]; then
        echo "Step 3: Agent-based script generation available"
        echo "---------------------------------------------"
        echo "✅ All tests passed! You can now run:"
        echo "python experiment/main.py agents"
    else
        echo "❌ Agent test failed"
    fi
else
    echo "❌ Import test failed"
fi

echo ""
echo "Test complete!"