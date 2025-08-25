#!/bin/bash
# Start the working Supernote Demo Viewer with all requested features

echo "🚀 Starting Supernote Demo Viewer (Final Version)"
echo "=================================================="

# Kill existing session if it exists
tmux kill-session -t sn2md-demo 2>/dev/null || true

# Create new tmux session
tmux new-session -d -s sn2md-demo -c /home/ed/ghost-writer

# Start the demo viewer
tmux send-keys -t sn2md-demo "cd /home/ed/ghost-writer" C-m
tmux send-keys -t sn2md-demo "source .venv/bin/activate" C-m
tmux send-keys -t sn2md-demo "python web_viewer_demo_simple.py" C-m

echo "✅ Demo Viewer is running!"
echo ""
echo "📍 ACCESS: http://100.111.114.84:5000"
echo ""
echo "🎯 DEMO FEATURES IMPLEMENTED:"
echo "   ✅ Demo Mode Toggle (15-second auto-refresh)"
echo "   ✅ Manual 'Check for New Notes' button"
echo "   ✅ joe.note always available as fallback"
echo "   ✅ Single VISIBLE mode extraction (no duplicates)"
echo "   ✅ Note selection interface"
echo "   ✅ Auto-authentication with provided credentials"
echo "   ✅ Both Local (Ollama) and OpenAI transcription"
echo "   ✅ Fresh note detection with 🔥 badges"
echo ""
echo "🎬 DEMO FLOW:"
echo "1. Page loads with joe.note ready to process"
echo "2. Toggle Demo Mode ON for live cloud sync"
echo "3. Write note on Supernote device and sync"
echo "4. Watch as fresh notes appear with 🔥 FRESH badge"
echo "5. Select any note and click 'Process'"
echo "6. Compare Local vs OpenAI transcription results"
echo ""
echo "⚙️  TMUX COMMANDS:"
echo "   View logs:    tmux attach -t sn2md-demo"
echo "   Detach:       Ctrl+B, then D"
echo "   Stop server:  tmux kill-session -t sn2md-demo"
echo ""
echo "🎪 Ready for your demo!"