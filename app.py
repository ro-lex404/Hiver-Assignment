import sys
import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Insert project root into sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.pipeline import SupportAgentPipeline
from src.evaluation.llm_judge import LLMJudgeRubric

pipeline = SupportAgentPipeline()
judge = LLMJudgeRubric()

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hiver AI Customer Support Agent & Evaluation Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; }
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .accent-gradient { background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-6xl mx-auto space-y-6">
        
        <!-- Header -->
        <header class="glass rounded-2xl p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl accent-gradient flex items-center justify-center text-white shadow-lg">
                        <i class="fa-solid fa-headset text-lg"></i>
                    </div>
                    <div>
                        <h1 class="text-2xl font-bold tracking-tight">Hiver AI Customer Support Agent</h1>
                        <p class="text-sm text-slate-400">Production RAG Pipeline &bull; Multi-Signal Escalation &bull; LLM-as-a-Judge</p>
                    </div>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <span class="px-3 py-1 text-xs rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    <i class="fa-brands fa-twitter mr-1"></i> @AmazonHelp SOPs
                </span>
                <span class="px-3 py-1 text-xs rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    <i class="fa-solid fa-bolt mr-1"></i> Live Active
                </span>
            </div>
        </header>

        <!-- Main Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            <!-- Left Column: Input & Presets -->
            <div class="lg:col-span-5 space-y-6">
                
                <!-- Input Box -->
                <div class="glass rounded-2xl p-6 space-y-4">
                    <h2 class="text-lg font-semibold flex items-center gap-2">
                        <i class="fa-solid fa-comment-dots text-indigo-400"></i> Incoming Customer Tweet
                    </h2>
                    <textarea id="tweetInput" rows="4" class="w-full bg-slate-900/90 border border-slate-700 rounded-xl p-3 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none placeholder-slate-500" placeholder="Type a customer tweet or choose from presets below..."></textarea>
                    
                    <div class="flex justify-between items-center text-xs text-slate-400">
                        <span id="charCount">0 / 280 chars</span>
                        <button onclick="processTweet()" id="submitBtn" class="accent-gradient hover:opacity-90 px-5 py-2.5 rounded-xl font-medium text-white shadow-md transition-all flex items-center gap-2">
                            <i class="fa-solid fa-paper-plane"></i> Run Agent
                        </button>
                    </div>
                </div>

                <!-- Presets -->
                <div class="glass rounded-2xl p-6 space-y-3">
                    <h3 class="text-sm font-semibold text-slate-300">Quick Test Scenarios</h3>
                    <div class="space-y-2">
                        <button onclick="setPreset(0)" class="w-full text-left p-2.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 text-xs text-slate-300 transition border border-slate-700/50">
                            <span class="text-indigo-400 font-semibold">[Late Package]</span> Tracking TBA9823 says delivered but porch is empty!
                        </button>
                        <button onclick="setPreset(1)" class="w-full text-left p-2.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 text-xs text-slate-300 transition border border-slate-700/50">
                            <span class="text-emerald-400 font-semibold">[Self-Service Return]</span> How do I drop off a return at Whole Foods?
                        </button>
                        <button onclick="setPreset(2)" class="w-full text-left p-2.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 text-xs text-slate-300 transition border border-slate-700/50">
                            <span class="text-red-400 font-semibold">[Security Alert]</span> My account email was changed and $700 charged!
                        </button>
                        <button onclick="setPreset(3)" class="w-full text-left p-2.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 text-xs text-slate-300 transition border border-slate-700/50">
                            <span class="text-amber-400 font-semibold">[Hazard / Legal]</span> Blender started smoking and threw sparks in kitchen!
                        </button>
                    </div>
                </div>

            </div>

            <!-- Right Column: Agent Output & Evaluation -->
            <div class="lg:col-span-7 space-y-6">
                
                <!-- Live Pipeline Result Card -->
                <div id="resultCard" class="glass rounded-2xl p-6 space-y-5 hidden">
                    
                    <!-- Status Header -->
                    <div class="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-700/60">
                        <div>
                            <span class="text-xs text-slate-400 block">Classified Intent</span>
                            <span id="resIntent" class="text-base font-bold text-indigo-400">-</span>
                            <span id="resConfidence" class="text-xs text-slate-400 ml-2">(Conf: -)</span>
                        </div>
                        <div id="escalationBadge" class="px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5">
                            -
                        </div>
                    </div>

                    <!-- Stated Reason -->
                    <div class="bg-slate-900/60 rounded-xl p-3 border border-slate-800 text-xs">
                        <span class="text-slate-400 font-semibold block mb-1">
                            <i class="fa-solid fa-shield-halved mr-1 text-slate-400"></i> Escalation Rationale / Audit Log:
                        </span>
                        <p id="resReason" class="text-slate-300">-</p>
                    </div>

                    <!-- Draft Reply -->
                    <div class="space-y-2">
                        <div class="flex justify-between text-xs text-slate-400">
                            <span class="font-semibold text-slate-300 flex items-center gap-1.5">
                                <i class="fa-brands fa-twitter text-sky-400"></i> Grounded Draft Reply (<280 chars)
                            </span>
                            <span id="replyLen">0 chars</span>
                        </div>
                        <div class="bg-slate-950/80 rounded-xl p-4 border border-slate-800/80 text-sm leading-relaxed text-slate-100" id="resReply">
                            -
                        </div>
                    </div>

                    <!-- Retrieved RAG Historical Context -->
                    <div class="space-y-2">
                        <span class="text-xs font-semibold text-slate-400 flex items-center gap-1">
                            <i class="fa-solid fa-database text-purple-400"></i> Top-1 Retrieved Historical Resolution Pair
                        </span>
                        <div class="bg-slate-900/80 rounded-xl p-3 border border-slate-800/60 text-xs text-slate-300 space-y-1">
                            <p class="text-slate-400"><strong>Query:</strong> <span id="ragQuery">-</span></p>
                            <p class="text-slate-300"><strong>Resolution:</strong> <span id="ragResolution">-</span></p>
                        </div>
                    </div>

                    <!-- LLM Judge Live Score -->
                    <div class="bg-gradient-to-r from-indigo-950/40 to-purple-950/40 rounded-xl p-4 border border-indigo-500/20 space-y-3">
                        <div class="flex justify-between items-center">
                            <span class="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                                <i class="fa-solid fa-gavel text-amber-400"></i> LLM-as-a-Judge Live Quality Audit
                            </span>
                            <span id="judgeOverall" class="text-sm font-bold text-emerald-400">Overall: - / 5.0</span>
                        </div>
                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                            <div class="bg-slate-900/60 rounded-lg p-2 border border-slate-800">
                                <span class="text-slate-400 block">Groundedness</span>
                                <span id="jGrounded" class="font-bold text-slate-200">-</span>
                            </div>
                            <div class="bg-slate-900/60 rounded-lg p-2 border border-slate-800">
                                <span class="text-slate-400 block">Helpfulness</span>
                                <span id="jHelpful" class="font-bold text-slate-200">-</span>
                            </div>
                            <div class="bg-slate-900/60 rounded-lg p-2 border border-slate-800">
                                <span class="text-slate-400 block">Tone & Safety</span>
                                <span id="jTone" class="font-bold text-slate-200">-</span>
                            </div>
                            <div class="bg-slate-900/60 rounded-lg p-2 border border-slate-800">
                                <span class="text-slate-400 block">Escalation</span>
                                <span id="jEsc" class="font-bold text-slate-200">-</span>
                            </div>
                        </div>
                    </div>

                    <!-- Latency -->
                    <div class="text-right text-[11px] text-slate-500">
                        Execution Latency: <span id="resLatency" class="text-slate-400 font-mono">-</span>
                    </div>

                </div>

                <!-- Empty State Placeholder -->
                <div id="emptyCard" class="glass rounded-2xl p-12 text-center space-y-3">
                    <i class="fa-solid fa-wand-magic-sparkles text-4xl text-indigo-400/50 mb-2"></i>
                    <h3 class="text-lg font-semibold text-slate-300">Agent Ready for Evaluation</h3>
                    <p class="text-xs text-slate-500 max-w-sm mx-auto">Enter a customer support query or select a preset scenario to view real-time intent routing, RAG grounding, escalation, and automated judge scoring.</p>
                </div>

            </div>

        </div>

    </div>

    <script>
        const presets = [
            "Tracking TBA982348123019 says delivered on porch at 3 PM but nothing is here! Look into my account ASAP!",
            "How long do I have to return an unopened item at Whole Foods or Kohl's?",
            "My account email was changed without permission and someone charged $700 for an iPhone! Help!",
            "The electric blender started smoking and threw sparks all over my kitchen counter!"
        ];

        function setPreset(idx) {
            document.getElementById("tweetInput").value = presets[idx];
            updateCount();
            processTweet();
        }

        const tweetInput = document.getElementById("tweetInput");
        tweetInput.addEventListener("input", updateCount);

        function updateCount() {
            const len = tweetInput.value.length;
            document.getElementById("charCount").innerText = `${len} / 280 chars`;
        }

        async function processTweet() {
            const text = tweetInput.value.trim();
            if (!text) return;

            const btn = document.getElementById("submitBtn");
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Processing...`;
            btn.disabled = true;

            try {
                const resp = await fetch("/api/process", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text })
                });
                const data = await resp.json();

                document.getElementById("emptyCard").classList.add("hidden");
                document.getElementById("resultCard").classList.remove("hidden");

                document.getElementById("resIntent").innerText = data.intent;
                document.getElementById("resConfidence").innerText = `(Confidence: ${(data.confidence * 100).toFixed(1)}%)`;

                const escBadge = document.getElementById("escalationBadge");
                if (data.escalation.should_escalate) {
                    escBadge.className = "px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/40 flex items-center gap-1.5";
                    escBadge.innerHTML = `<i class="fa-solid fa-user-shield"></i> ESCALATED TO HUMAN`;
                } else {
                    escBadge.className = "px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5";
                    escBadge.innerHTML = `<i class="fa-solid fa-robot"></i> AUTO-HANDLED (SELF-SERVICE)`;
                }

                document.getElementById("resReason").innerText = data.escalation.stated_reason;
                document.getElementById("resReply").innerText = data.draft_reply;
                document.getElementById("replyLen").innerText = `${data.draft_reply.length} chars`;
                document.getElementById("resLatency").innerText = `${data.latency_ms} ms`;

                if (data.retrieved_context && data.retrieved_context.length > 0) {
                    document.getElementById("ragQuery").innerText = data.retrieved_context[0].query;
                    document.getElementById("ragResolution").innerText = data.retrieved_context[0].resolution;
                } else {
                    document.getElementById("ragQuery").innerText = "Standard Brand SOP Rule";
                    document.getElementById("ragResolution").innerText = "amazon.com/help";
                }

                // Judge Ratings
                const j = data.judge;
                document.getElementById("judgeOverall").innerText = `Overall: ${j.overall_score.toFixed(2)} / 5.0`;
                document.getElementById("jGrounded").innerText = `${j.groundedness} / 5`;
                document.getElementById("jHelpful").innerText = `${j.helpfulness} / 5`;
                document.getElementById("jTone").innerText = `${j.tone_safety} / 5`;
                document.getElementById("jEsc").innerText = `${j.escalation_appropriateness} / 5`;

            } catch (err) {
                alert("Error processing tweet: " + err);
            } finally {
                btn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Run Agent`;
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
"""

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self):
        if self.path == "/api/process":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            query = body.get("text", "")

            # Run agent pipeline
            result = pipeline.process(query)

            # Run live LLM judge audit
            judge_res = judge.evaluate_reply(
                customer_text=query,
                predicted_reply=result["draft_reply"],
                predicted_intent=result["intent"],
                predicted_escalation=result["escalation"]["should_escalate"],
                true_intent=result["intent"],
                true_escalation=result["escalation"]["should_escalate"],
                reference_reply=result["draft_reply"]
            )
            result["judge"] = judge_res

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))

def main():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), RequestHandler)
    url = f"http://localhost:{port}"
    print(f"\\n========================================================")
    print(f"  Hiver AI Customer Support Dashboard Server Running")
    print(f"  Access UI at: {url}")
    print(f"========================================================\\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nShutting down server.")

if __name__ == "__main__":
    main()
