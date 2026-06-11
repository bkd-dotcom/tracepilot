# TracePilot: Step-by-Step Preview

Welcome to the TracePilot preview! This guide walks you through exactly how the platform works using screenshots from a live demonstration. 

We will watch the agent make a mistake, audit its own trace data, **learn from the error**, and **self-heal** to successfully route the user to the correct information—all while tracking cost, latency, and helpfulness metrics.

---

## Step 1: The Initial Query (Exploring a New Path)

A user enters a query into the TracePilot UI asking for internal company policy: 
> *"Find employee handbook section 7.3"*

<p align="center">
  <img src="images/Platform_Image/ui_01_first_query.png" width="80%">
</p>

### The Routing Decision
Because this is a brand new category of query, the agent has **no historical memory**. It defaults to its highest-ranked default tool: `web_search`. This is called **"Explore Mode"**.

<p align="center">
  <img src="images/term_01_query.png" width="80%">
  <br>
  <img src="images/term_02_routing.png" width="80%">
</p>

### The Failure & Metric Logging
Since an employee handbook isn't on the public internet, the web search fails immediately with an **Access Denied** error. 

Notice how TracePilot logs the **cost ($0.12)** and **latency (9.5s)** of this failed attempt. These metrics form the basis of its "Economic Memory".

<p align="center">
  <img src="images/term_03_result.png" width="80%">
  <br>
  <img src="images/term_04_confidence.png" width="80%">
</p>

### The Live LLM Jury Evaluation
In the background, TracePilot evaluates the OpenTelemetry trace of this interaction. Because the tool failed and provided no value, the Jury accurately penalizes the attempt:
* **Helpfulness: 0.0**
* **Efficiency: 0.0**

<p align="center">
  <img src="images/term_05_eval.png" width="80%">
  <br>
  <img src="images/term_06_eval2.png" width="80%">
  <br>
  <img src="images/term_07_eval3.png" width="80%">
</p>

---

## Step 2: The MCP Auditor (Correcting the Mistake)

In a traditional agent setup, a developer would have to manually read logs to figure out why the agent hallucinated and used the web search. With TracePilot, we trigger the autonomous **Auditor Agent**.

<p align="center">
  <img src="images/Platform_Image/ui_02_audit_click.png" width="80%">
</p>

### Identifying Hidden Failures
The Auditor Agent connects to the **Arize Phoenix MCP Server**. It reads the recent traces, identifies the "Access Denied" error, and realizes that `web_search` is a terrible tool for internal queries. 

It autonomously adjusts the internal **Confidence Score** for `web_search` downward.

<p align="center">
  <img src="images/term_08_auditor.png" width="80%">
  <br>
  <img src="images/term_09_audit_summary.png" width="80%">
</p>

---

## Step 3: The Self-Healing Re-Query (Exploiting the Right Path)

The user enters the exact same query again.

<p align="center">
  <img src="images/Platform_Image/ui_03_second_query.png" width="80%">
  <br>
  <img src="images/term_10_requery.png" width="80%">
</p>

### Autonomous Rerouting
Because `web_search` was penalized during the audit, its confidence score is now too low. The agent avoids it entirely and explores the next logical tool: `uploaded_documents`.

<p align="center">
  <img src="images/term_11_explore.png" width="80%">
</p>

### The Success
The `uploaded_documents` tool successfully retrieves the internal handbook! 

Notice the massive improvements in the Economic Memory:
* **Success Rate:** Jumped to 100% for this tool.
* **Confidence Score:** Spiked into the green zone (Exploit Mode).
* **Latency & Cost:** Dramatically lower than the web search.

<p align="center">
  <img src="images/Platform_Image/ui_04_success.png" width="80%">
  <br>
  <img src="images/term_12_success.png" width="80%">
  <br>
  <img src="images/term_13_new_confidence.png" width="80%">
</p>

### The Final Evaluation
The Live LLM Jury reviews the new trace and awards the agent a perfect score:
* **Helpfulness: 1.0**
* **Efficiency: 1.0**

<p align="center">
  <img src="images/term_14_new_eval.png" width="80%">
</p>

---

### Conclusion
TracePilot successfully **self-healed**. Without any developer intervention, prompt engineering, or manual routing rules, the agent learned from its telemetry traces, penalized the wrong tool, and found the correct path. 

All future queries of this type will instantly bypass the exploration phase and utilize the `uploaded_documents` tool with maximum efficiency!
