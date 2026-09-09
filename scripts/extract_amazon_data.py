import sys
import json
import csv
from pathlib import Path

csv_path = Path("customer-support-on-twitter/twcs/twcs.csv")
out_dir = Path("data/processed")
out_dir.mkdir(parents=True, exist_ok=True)

print("Starting fast streaming extraction for @AmazonHelp from twcs.csv...")

# Pass 1: Collect AmazonHelp responses and the customer tweet IDs they responded to
# columns: tweet_id, author_id, inbound, created_at, text, response_tweet_id, in_response_to_tweet_id
amazon_replies = {} # in_response_to_tweet_id -> agent_text
needed_customer_ids = set()

count = 0
with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
    reader = csv.reader(f)
    header = next(reader) # skip header
    for row in reader:
        count += 1
        if len(row) >= 7:
            tweet_id, author_id, inbound, created_at, text, resp_id, in_resp_id = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
            if author_id.strip().lower() == "amazonhelp" and in_resp_id:
                amazon_replies[in_resp_id] = {
                    "agent_tweet_id": tweet_id,
                    "agent_text": text,
                    "created_at": created_at
                }
                needed_customer_ids.add(in_resp_id)

print(f"Pass 1 complete. Scanned {count:,} rows.")
print(f"Found {len(amazon_replies):,} AmazonHelp responses linked to customer inquiries.")

# Pass 2: Stream through twcs.csv again to match customer query text
matched_pairs = []
with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if len(row) >= 7:
            tweet_id, author_id, inbound, created_at, text = row[0], row[1], row[2], row[3], row[4]
            if tweet_id in amazon_replies:
                agent_info = amazon_replies[tweet_id]
                matched_pairs.append({
                    "customer_tweet_id": tweet_id,
                    "customer_author_id": author_id,
                    "customer_text": text,
                    "agent_tweet_id": agent_info["agent_tweet_id"],
                    "agent_text": agent_info["agent_text"],
                    "created_at": agent_info["created_at"]
                })

print(f"Pass 2 complete. Successfully reconstructed {len(matched_pairs):,} exact (Customer -> Agent) resolution pairs!")

# Save top 10,000 clean pairs for RAG Knowledge Base and Golden Set analysis
qa_out_path = out_dir / "amazon_qa_pairs_10k.jsonl"
with open(qa_out_path, "w", encoding="utf-8") as f:
    for pair in matched_pairs[:10000]:
        f.write(json.dumps(pair) + "\n")

print(f"Saved 10,000 verified QA resolution pairs to {qa_out_path}")
