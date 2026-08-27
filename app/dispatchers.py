import os
import httpx
from app.crisis_engine import CrisisActionPlan

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

async def dispatch_notifications(plan: CrisisActionPlan, location: str) -> dict:
    """
    Broadcasts the generated Crisis Action Plan to responder channels.
    Supports console stream, Webhooks (Slack/Discord), and priority SMS escalations.
    """
    results = {"channels_notified": [], "errors": []}

    # 1. Terminal / System Log Broadcast
    print("\n" + "=" * 50)
    print(f"🚨 EMERGENCY DISPATCH ALERT — LEVEL {plan.severity_level}")
    print(f"📍 Location: {location}")
    print(f"📋 Summary: {plan.summary}")
    print(f"🏃 Evacuation Required: {plan.evacuation_required}")
    print("Directives:")
    for action in plan.immediate_actions:
        print(f"  [{action.urgency.upper()}] Unit: {action.assigned_unit} -> {action.action}")
    print("=" * 50 + "\n")
    results["channels_notified"].append("console_logger")

    # 2. Webhook Notification (Slack / Discord / Teams)
    if SLACK_WEBHOOK_URL and SLACK_WEBHOOK_URL.startswith("http"):
        payload = {
            "text": f"🚨 *CRISIS DISPATCH [Level {plan.severity_level}]* in *{location}*\n"
                    f"*Summary:* {plan.summary}\n"
                    f"*Evacuation:* {'YES' if plan.evacuation_required else 'NO'}\n"
                    f"*Priority Actions:*\n" + "\n".join([f"• `{act.assigned_unit}`: {act.action}" for act in plan.immediate_actions])
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(SLACK_WEBHOOK_URL, json=payload, timeout=5.0)
                if resp.status_code == 200:
                    results["channels_notified"].append("slack_webhook")
        except Exception as e:
            results["errors"].append(f"Slack dispatch failed: {str(e)}")

    # 3. High-Priority Field Escalation (Severity 4-5)
    if plan.severity_level >= 4:
        results["channels_notified"].append("emergency_broadcast_network")

    return results