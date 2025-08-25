#!/bin/bash
# Start sn2md web viewer in tmux session for persistent access

echo "Starting sn2md Web Viewer in tmux session..."
echo "============================================"

# Check if session already exists
if tmux has-session -t sn2md-demo 2>/dev/null; then
    echo "Session 'sn2md-demo' already exists!"
    echo "To attach: tmux attach -t sn2md-demo"
    echo "To kill it first: tmux kill-session -t sn2md-demo"
    exit 1
fi

# Create new tmux session and run the web viewer
tmux new-session -d -s sn2md-demo -c /home/ed/ghost-writer

# Send commands to the tmux session
tmux send-keys -t sn2md-demo "cd /home/ed/ghost-writer" C-m
tmux send-keys -t sn2md-demo "source .venv/bin/activate" C-m
tmux send-keys -t sn2md-demo "echo '🚀 Starting sn2md Web Viewer...'" C-m
tmux send-keys -t sn2md-demo "echo '📍 Access at: http://100.111.114.84:5000'" C-m
tmux send-keys -t sn2md-demo "echo ''" C-m
tmux send-keys -t sn2md-demo "python web_viewer_fixed.py" C-m

echo "✅ sn2md Web Viewer started in tmux session 'sn2md-demo'"
echo ""
echo "📍 Access the viewer at: http://100.111.114.84:5000"
echo ""
echo "tmux commands:"
echo "  Attach to session:  tmux attach -t sn2md-demo"
echo "  Detach from session: Ctrl+B, then D"
echo "  List sessions:      tmux ls"
echo "  Kill session:       tmux kill-session -t sn2md-demo"
echo ""
echo "The viewer will keep running even if you disconnect!"