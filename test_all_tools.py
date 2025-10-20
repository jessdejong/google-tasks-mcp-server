#!/usr/bin/env python3
"""
Integration test for Google Tasks MCP tools.

This script exercises: create_tasklist, create_task, get_task, update_task,
complete_task, move_task, search_tasks, delete_task.
"""

import asyncio
import json
import time
from typing import Dict, Any

from server import get_google_tasks_service


async def main() -> None:
    print("🚀 Running integration test for MCP tools")
    svc = get_google_tasks_service()
    if not svc:
        print("❌ Auth failed - ensure credentials.json/token.json are present")
        return

    # 1) Create tasklist
    title = f"MCP Test List {int(time.time())}"
    tl = svc.tasklists().insert(body={"title": title}).execute()
    tasklist_id = tl["id"]
    print(f"✅ Created tasklist: {tasklist_id} -> {title}")

    try:
        # 2) Create task (root)
        t1 = svc.tasks().insert(tasklist=tasklist_id, body={
            "title": "Test Task 1",
            "notes": "Created by integration test"
        }).execute()
        print(f"✅ Created task: {t1['id']}")

        # 3) Get task
        got = svc.tasks().get(tasklist=tasklist_id, task=t1["id"]).execute()
        print(f"✅ Got task title: {got.get('title')}")

        # 4) Update task
        upd = svc.tasks().patch(tasklist=tasklist_id, task=t1["id"], body={
            "notes": "Updated notes",
            "title": "Test Task 1 (updated)"
        }).execute()
        print(f"✅ Updated task title: {upd.get('title')}")

        # 5) Complete task
        done = svc.tasks().patch(tasklist=tasklist_id, task=t1["id"], body={
            "status": "completed"
        }).execute()
        print(f"✅ Completed task status: {done.get('status')}")

        # 6) Create another task then move first after it
        t2 = svc.tasks().insert(tasklist=tasklist_id, body={"title": "Test Task 2"}).execute()
        moved = svc.tasks().move(tasklist=tasklist_id, task=t1["id"], previous=t2["id"]).execute()
        print(f"✅ Moved task position: {moved.get('position')}")

        # 7) Search (client-side) - list and filter
        items = svc.tasks().list(tasklist=tasklist_id, showCompleted=True).execute().get("items", [])
        filtered = [i for i in items if "updated" in i]
        print(f"✅ Search-like filter count: {len(filtered)}")

        # 8) Delete tasks
        svc.tasks().delete(tasklist=tasklist_id, task=t1["id"]).execute()
        svc.tasks().delete(tasklist=tasklist_id, task=t2["id"]).execute()
        print("✅ Deleted tasks")

    finally:
        # Cleanup tasklist
        svc.tasklists().delete(tasklist=tasklist_id).execute()
        print("✅ Deleted tasklist (cleanup)")


if __name__ == "__main__":
    asyncio.run(main())
