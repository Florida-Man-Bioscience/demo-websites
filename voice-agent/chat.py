"""Test the sales agent in your terminal — no Twilio needed.

Simulates a call: you type what the business owner says, the agent replies
with text and (with --voice) speaks each reply through Sesame CSM via your
speakers. SMS sending is stubbed to a printout, so nothing real is texted.

    python chat.py --list-slugs            # find a business to role-play
    python chat.py ole-barn                # text-only outbound call sim
    python chat.py ole-barn --voice        # with spoken audio
    python chat.py ole-barn --inbound      # simulate them calling you back

Ctrl-C or an agent hang-up ends the session. Outcomes still go to
call-log.csv so you can see what would be recorded (rows are tagged
call_sid=TEST-... so they don't pollute the real queue: delete them, or
leave them — call.py --next skips slugs present in the log).
"""

import argparse
import shutil
import subprocess
import sys

import agent
import config
import tts
from agent import CallState, run_turn
from businesses import all_businesses, by_slug


def find_player() -> list[str] | None:
    for cmd in (["paplay"], ["pw-play"], ["aplay", "-q"], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]):
        if shutil.which(cmd[0]):
            return cmd
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", nargs="?", help="business slug to role-play")
    parser.add_argument("--voice", action="store_true", help="speak replies with Sesame TTS")
    parser.add_argument("--inbound", action="store_true", help="simulate an inbound callback")
    parser.add_argument("--list-slugs", action="store_true")
    args = parser.parse_args()

    if args.list_slugs:
        for b in all_businesses()[:30]:
            print(f"{b.slug:45s} {b.category}")
        print("... (see correspondences/outreach-data.csv for all 252)")
        return

    if not args.slug:
        parser.error("give a business slug (try --list-slugs)")
    business = by_slug(args.slug)
    if business is None:
        sys.exit(f"No business found for slug {args.slug!r}")

    config.require("ANTHROPIC_API_KEY")
    if args.voice:
        config.require("DEEPINFRA_API_KEY")
    player = find_player() if args.voice else None
    if args.voice and player is None:
        sys.exit("No audio player found (need paplay, pw-play, aplay, or ffplay)")

    # Never send a real SMS from the simulator.
    agent._send_sms = lambda state, to: (
        print(f"\n  [SIM] would text demo link to {to or state.caller_number or 'caller'}\n"),
        "SMS with the demo link sent.",
    )[1]

    direction = "inbound" if args.inbound else "outbound"
    state = CallState(
        call_sid=f"TEST-{business.slug}",
        business=business,
        direction=direction,
        caller_number="+13525550199",
    )

    print(f"--- Simulated {direction} call: {business.name} ({business.category}) ---")
    print(f"--- Demo site: {business.demo_url}")
    print("--- You are the business owner. Type replies; Ctrl-C to quit. ---\n")

    def speak(text: str):
        print(f"AGENT: {text}\n")
        if player:
            try:
                key = tts.synthesize(text)
                subprocess.run(player + [str(tts.audio_path(key))], check=False)
            except Exception as e:
                print(f"  [voice unavailable: {e}]")

    try:
        speak(run_turn(state, None))
        while not state.ended:
            user = input("YOU:   ").strip()
            speak(run_turn(state, user or None))
    except (KeyboardInterrupt, EOFError):
        print("\n--- simulation ended ---")
        return
    print("--- agent hung up ---")


if __name__ == "__main__":
    main()
