#!/bin/bash
# Start enhanced demo web viewer with all new features

echo "Starting Enhanced Supernote Demo Viewer..."
echo "=========================================="

# Check if session already exists
if tmux has-session -t sn2md-demo 2>/dev/null; then
    echo "Session 'sn2md-demo' already exists!"
    echo "To attach: tmux attach -t sn2md-demo"
    echo "To kill it first: tmux kill-session -t sn2md-demo"
    exit 1
fi

# Create new tmux session and run the enhanced viewer
tmux new-session -d -s sn2md-demo -c /home/ed/ghost-writer

# Send commands to the tmux session
tmux send-keys -t sn2md-demo "cd /home/ed/ghost-writer" C-m
tmux send-keys -t sn2md-demo "source .venv/bin/activate" C-m
tmux send-keys -t sn2md-demo "echo '🚀 Starting Enhanced Demo Viewer...'" C-m
tmux send-keys -t sn2md-demo "echo ''" C-m
tmux send-keys -t sn2md-demo "echo '✨ FEATURES:'" C-m
tmux send-keys -t sn2md-demo "echo '  • Demo Mode: Auto-check every 15 seconds'" C-m
tmux send-keys -t sn2md-demo "echo '  • Normal Mode: Manual checking only'" C-m
tmux send-keys -t sn2md-demo "echo '  • Note Selection: Choose multiple notes'" C-m
tmux send-keys -t sn2md-demo "echo '  • Single Extraction: VISIBLE mode only'" C-m
tmux send-keys -t sn2md-demo "echo '  • Fresh Badge: Shows recently created notes'" C-m
tmux send-keys -t sn2md-demo "echo ''" C-m
tmux send-keys -t sn2md-demo "echo '📍 Access at: http://100.111.114.84:5000'" C-m
tmux send-keys -t sn2md-demo "echo ''" C-m
tmux send-keys -t sn2md-demo "python web_viewer_demo.py" C-m

echo "✅ Enhanced Demo Viewer started in tmux session 'sn2md-demo'"
echo ""
echo "📍 Access the viewer at: http://100.111.114.84:5000"
echo ""
echo "🎬 Demo Flow:"
echo "1. Toggle 'Demo Mode' to ON for auto-refresh"
echo "2. Write note on Supernote and sync"
echo "3. Watch as new note appears with 🔥 FRESH badge"
echo "4. Select note(s) and click Process"
echo "5. Compare Local vs OpenAI transcription"
echo ""
echo "tmux commands:"
echo "  Attach to session:  tmux attach -t sn2md-demo"
echo "  Detach from session: Ctrl+B, then D"
echo "  Kill session:       tmux kill-session -t sn2md-demo"
echo ""
echo "The viewer will keep running even if you disconnect!"