#!/bin/bash

# Monitor scraper progress and commit/push every 5 minutes
cd /home/user/novel

while true; do
    sleep 300  # Wait 5 minutes

    # Count current chapters
    CHAPTER_COUNT=$(ls 帝霸/*.md 2>/dev/null | wc -l)

    # Check if scraper is still running
    if ! pgrep -f "python.*scraper.py" > /dev/null; then
        echo "[$(date)] Scraper finished or stopped. Final count: $CHAPTER_COUNT chapters"

        # Final commit and push
        git add 帝霸/*.md
        git commit -m "feat: 新增章節 (total: $CHAPTER_COUNT chapters)

https://claude.ai/code/session_01CjavGbnvftqkPqEvRCpdTp"
        git push -u origin claude/scrape-novel-to-markdown-t2DpU

        echo "[$(date)] Final push complete. Exiting monitor."
        exit 0
    fi

    # Check for new untracked files
    NEW_FILES=$(git status --porcelain 帝霸/*.md 2>/dev/null | grep "^??" | wc -l)

    if [ "$NEW_FILES" -gt 0 ]; then
        echo "[$(date)] Found $NEW_FILES new chapters. Total: $CHAPTER_COUNT. Committing..."

        # Add and commit new chapters
        git add 帝霸/*.md
        git commit -m "feat: 新增章節 (progress: $CHAPTER_COUNT / 7227 chapters)

https://claude.ai/code/session_01CjavGbnvftqkPqEvRCpdTp"

        # Push with retry
        for i in 1 2 3 4; do
            if git push -u origin claude/scrape-novel-to-markdown-t2DpU; then
                echo "[$(date)] Push successful"
                break
            else
                echo "[$(date)] Push failed, retry $i..."
                sleep $((2 ** i))
            fi
        done
    else
        echo "[$(date)] No new chapters. Current: $CHAPTER_COUNT"
    fi
done
