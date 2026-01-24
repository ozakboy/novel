#!/bin/bash

# Monitor scraper progress and commit/push every 10 chapters
cd /home/user/novel

LAST_COUNT=0

while true; do
    sleep 30  # Check every 30 seconds

    # Count current chapters
    CHAPTER_COUNT=$(ls 帝霸/*.md 2>/dev/null | wc -l)

    # Check if scraper is still running
    if ! pgrep -f "python.*scraper.py" > /dev/null; then
        echo "[$(date)] Scraper finished or stopped. Final count: $CHAPTER_COUNT chapters"

        # Final commit and push
        git add 帝霸/*.md scraper.py
        git commit -m "feat: 完成所有章節下載 (total: $CHAPTER_COUNT chapters)

https://claude.ai/code/session_01CjavGbnvftqkPqEvRCpdTp"
        git push -u origin claude/scrape-novel-to-markdown-t2DpU

        echo "[$(date)] Final push complete. Exiting monitor."
        exit 0
    fi

    # Calculate new chapters since last commit
    NEW_CHAPTERS=$((CHAPTER_COUNT - LAST_COUNT))

    # Commit every 10 new chapters
    if [ "$NEW_CHAPTERS" -ge 10 ]; then
        echo "[$(date)] Progress: $CHAPTER_COUNT / 7227 chapters (+$NEW_CHAPTERS new). Committing..."

        # Add and commit new chapters
        git add 帝霸/*.md
        git commit -m "feat: 新增章節 (progress: $CHAPTER_COUNT / 7227 chapters)

https://claude.ai/code/session_01CjavGbnvftqkPqEvRCpdTp"

        # Push with retry
        for i in 1 2 3 4; do
            if git push -u origin claude/scrape-novel-to-markdown-t2DpU; then
                echo "[$(date)] Push successful"
                LAST_COUNT=$CHAPTER_COUNT
                break
            else
                echo "[$(date)] Push failed, retry $i..."
                sleep $((2 ** i))
            fi
        done
    fi
done
